#!/bin/bash

if [ $# -lt 2 ]; then
    echo "Usage: $0 [action: create-branch/push-yml] [branch-name/config-file-path]"
    exit 1
fi

org_name="quic-qrb-ros"
action_yml_name="quic-organization-repolinter.yml"

action=$1
param=$2

excluded_repos=(
"quic-qrb-ros.github.io"
"rviz"
"ros2cli"
"ros2_tracing"
"meta-ros"
".github"
)

repos=$(gh api /orgs/$org_name/repos | jq '.[].name')

create_branches() {
    branch_name=$1
    for repo_raw in $repos; do
        repo=$(echo $repo_raw | tr -d '"')
        echo "Checking repo: $repo"
        excluded=false
        for excluded_repo in "${excluded_repos[@]}"; do
            if [[ $repo =~ $excluded_repo ]]; then
                excluded=true
                break
            fi
        done
        if $excluded; then
            echo "Skipping excluded repo: $repo"
            continue
        fi
        gh api /repos/$org_name/$repo/git/refs -X POST -F ref="refs/heads/$branch_name" -F sha="$(gh api /repos/$org_name/$repo/branches/master | jq -r '.commit.sha')"
    done
}

push_yml_file() {
    yml_file_path=$1
    for repo_raw in $repos; do
        repo=$(echo $repo_raw | tr -d '"')
        echo "Checking repo: $repo"
        excluded=false
        for excluded_repo in "${excluded_repos[@]}"; do
            if [[ $repo =~ $excluded_repo ]]; then
                excluded=true
                break
            fi
        done
        if $excluded; then
            echo "Skipping excluded repo: $repo"
            continue
        fi
        file_response=$(gh api /repos/$org_name/$repo/contents/.github/workflows/quic-organization-repolinter.yml)
        file_exists=$(echo $file_response | jq -r '.message' | grep -i 'not found')
        if [ -n "$file_exists" ]; then
            echo "Creating for $repo"
            encoded_content=$(cat $yml_file_path | base64)
            gh api /repos/$org_name/$repo/contents/.github/workflows/$action_yml_name -X PUT -F message="Create action" -F content="$encoded_content"
        else
            echo "Updating $repo"
            existing_sha=$(echo $file_response | jq -r '.sha')
            encoded_content=$(cat $yml_file_path | base64)
            gh api /repos/$org_name/$repo/contents/.github/workflows/$action_yml_name -X PUT -F message="Update action" -F content="$encoded_content" -F sha=$existing_sha
        fi
    done
}

if [ "$action" == "create-branch" ]; then
    create_branches $param
elif [ "$action" == "push-yml" ]; then
    push_yml_file $param
else
    echo "Invalid action. Use 'create-branch' or 'push-yml'."
    exit 1
fi
