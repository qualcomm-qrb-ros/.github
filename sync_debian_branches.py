#!/usr/bin/env python3
import os
import argparse
import json
import subprocess
import xml.etree.ElementTree as ET
from git import Repo, GitCommandError
from pathlib import Path

def find_ros_packages(path = "."):
    """Find ROS packages and return dict{path:name}"""
    packages = {}
    os.chdir(path)
    # Single package
    if Path("package.xml").exists():
        try:
            tree = ET.parse("package.xml")
            name = tree.findtext("name")
            packages["."] = name
        except ET.ParseError:
            print(f"Warning: {path}/package.xml parse failed!")
    else:   # Multiple packages
        for root, dirs, files in os.walk(path):
            if "package.xml" in files:
                try:
                    tree = ET.parse(Path(root) / "package.xml")
                    name = tree.findtext("name")
                    packages[root] = name
                    dirs.clear()
                except ET.ParseError:
                    print(f"Warning: {root}/package.xml parse failed!")
    return packages

def create_pull_request(target_branch, source_branch, commit, pr_num=None):
    title = f"Auto-sync: {commit.hexsha[:7]}"
    body = f"Source commit: {commit.hexsha}\nMessage: {commit.message.strip()}"
    if pr_num:
        body += f"\nOriginal PR: #{pr_num}"
    
    try:
        result = subprocess.run(
            ["gh", "pr", "create", 
             "--base", target_branch,
             "--head", source_branch,
             "--title", title,
             "--body", body,
             "--fill"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ PR created successfully: {result.stdout.strip()}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ PR creation failed: {e.stderr}")
        return None

def sync_commit_to_branch(repo, base_branch, target_branch, commit, files, packages, mode = "pr"):
    worktree_dir = f"worktree_{target_branch.replace('/', '_')}"
    worktree_path = Path(worktree_dir)
    pr_num = None

    try:
        repo.git.worktree("add", worktree_dir, target_branch)
        worktree_repo = Repo(worktree_path)
        
        for file in files:
            src_path = Path(file)

            # Remove path prefix
            for pkg_path in packages:
                if file.startswith(pkg_path + "/") or file == pkg_path:
                    relative_path = file[len(pkg_path):].lstrip("/")
                    dst_path = worktree_path / relative_path
                    break
            else:
                relative_path = file
                dst_path = worktree_path / relative_path

            dst_path.parent.mkdir(parents=True, exist_ok=True)

            print(f"📁 Copy from main: {file} -> debian: {relative_path}")
            repo.git.checkout(commit.hexsha, "--", file)
            if src_path.exists():
                with open(src_path, "rb") as f_src, open(dst_path, "wb") as f_dst:
                    f_dst.write(f_src.read())
        
        worktree_repo.git.add(A=True)
        if worktree_repo.is_dirty():

            original_msg = commit.message.strip()
            commit_msg = f"{original_msg}\nSource: {commit.hexsha}"
            
            if "Merge pull request" in original_msg:
                pr_num = original_msg.split("#")[1].split()[0]
                commit_msg += f" | PR: #{pr_num}"
            
            worktree_repo.index.commit(commit_msg)

            if mode == "direct":
                worktree_repo.git.push("origin", target_branch)
                print(f"✅ Push {commit.hexsha[:7]} to {target_branch}")
            else:
                temp_branch = f"sync-{target_branch.replace('/', '-')}-{commit.hexsha[:7]}"
                worktree_repo.git.checkout("-b", temp_branch)
                worktree_repo.git.push("origin", temp_branch, force=True)
                pr_url = create_pull_request(target_branch, temp_branch, commit, pr_num)
                if pr_url:
                    print(f"✅ PR created: {pr_url}")
        else:
            print(f"⏭️ {target_branch} nothing to commit")
    
    except GitCommandError as e:
        print(f"❌ Sync failed: {str(e)}")
    finally:
        if worktree_path.exists():
            repo.git.worktree("remove", worktree_dir, "--force")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Sync source to debian branch.")
    parser.add_argument("--mode", choices=["pr", "direct"], default="pr",
                        help="Sync mode, pr=Create a pull request(default), direct=Push to debian branch.")
    parser.add_argument("--path", type=str, default=".",
                        help="Path of workspace, default: current directory.")
    return parser.parse_args()

def main():
    args = parse_arguments()
    # Init repo
    repo = Repo(args.path)
    print("GH_TOKEN is set:", "GH_TOKEN" in os.environ)

    token = os.getenv("GITHUB_TOKEN")
    if token:
        origin_url = repo.remotes.origin.url
        authed_url = origin_url.replace("https://", f"https://x-access-token:{token}@")
        repo.remotes.origin.set_url(authed_url)

    # 1. Get packages
    packages = find_ros_packages(args.path)
    print(f"📦 Found {len(packages)} ROS packages: {json.dumps(packages, indent=2)}")

    # 2. Get commits
    before_sha = os.getenv("GITHUB_EVENT_BEFORE")
    after_sha = os.getenv("GITHUB_SHA")
    print(f"before_sha:{before_sha}, after_sha:{after_sha}")

    if not after_sha:
        print(f"Cannot get environment variable: GITHUB_SHA!")
        exit()

    if not before_sha or before_sha == "0"*40:  # Initial commit
        commits = [repo.commit(after_sha)]
    else:
        commits = list(repo.iter_commits(f"{before_sha}..{after_sha}"))
    
    print(f"🔍 Handle {len(commits)} commits.")
    print(f"🔍 Commits: {commits}")

    # 3. Process
    for commit in commits:
        try:
            # Get changed file list
            changed_files = [item.a_path for item in commit.diff(commit.parents[0])]
            print(f"Changed files: {changed_files}")
            affected_branches = {}
            
            # 4. Match packages
            for file in changed_files:
                for path, pkg_name in packages.items():
                    normalized_path = path[2:] if path.startswith("./") else path
                    print(f"\tnormalized_path:{normalized_path}, pkg_name:{pkg_name}, file:{file}")

                    if normalized_path == ".":
                        if "/" not in file or file.startswith("./"):
                            branch = f"debian/jazzy/noble/{pkg_name}"
                            affected_branches.setdefault(branch, set()).add(file)
                    else:
                        if file.startswith(normalized_path + "/") or file == normalized_path:
                            branch = f"debian/jazzy/noble/{pkg_name}"
                            affected_branches.setdefault(branch, set()).add(file)
            
            for branch, files in affected_branches.items():
                print(f"🔄 Sync {branch}: {len(files)} files. \nFiles: {files}")
                sync_commit_to_branch(repo, "main", branch, commit, files, packages, mode = args.mode)
        
        except IndexError:
            print(f"⚠️ Initial commit {commit.hexsha}. Skip file comparison")

if __name__ == "__main__":
    main()
