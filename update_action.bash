#!/bin/bash

org_name="quic-qrb-ros"
action_yml_name="quic-organization-repolinter.yml"

action_yaml_content='name: QuIC Organization Repolinter
on: [push, pull_request, workflow_dispatch]
jobs:
  repolinter:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repo
        uses: actions/checkout@v2
      - name: Verify repolinter config file is present
        id: check_files
        uses: andstor/file-existence-action@v1
        with:
          files: "repolint.json"
      - name: Run Repolinter with local repolint.json
        if: steps.check_files.outputs.files_exists == 'true'
        uses: todogroup/repolinter-action@v1
        with:
          config_file: "repolint.json"
      - name: Run Repolinter with default ruleset
        if: steps.check_files.outputs.files_exists == 'false'
        uses: todogroup/repolinter-action@v1
        with:
          config_url: "https://raw.githubusercontent.com/quic/.github/main/repolint.json"'

encoded_content=$(printf '%s' "$action_yaml_content" | base64)

excluded_repos=(
"quic-qrb-ros.github.io"
"rviz"
"ros2cli"
"ros2_tracing"
"meta-ros"
".github"
)

repos=$(gh api /orgs/$org_name/repos | jq '.[].name')

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
        gh api /repos/$org_name/$repo/contents/.github/workflows/$action_yml_name -X PUT -F message="Create action" -F content="$encoded_content"
    else
        echo "Updating $repo"
        existing_sha=$(echo $file_response | jq -r '.sha')
        gh api /repos/$org_name/$repo/contents/.github/workflows/$action_yml_name -X PUT -F message="Update action" -F content="$encoded_content" -F sha=$existing_sha
    fi
done
