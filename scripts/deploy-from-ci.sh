#!/usr/bin/env bash
# Transfer a CI-built image to the VPS and invoke its deployment script.
set -euo pipefail

## VALIDATE PREREQUISITES

deploy_sha="${1:?Missing deployment commit SHA}"
image_archive="${2:?Missing production image archive}"
known_hosts_file="${3:?Missing pinned known-hosts file}"

host="github@theodorblom.com"
quadlet_template="deploy/theodorblom.container.in"
vps_deploy_script="scripts/deploy-on-vps.sh"

if [[ ! "$deploy_sha" =~ ^[0-9a-f]{40}$ ]]; then
    echo "Invalid deployment commit SHA" >&2
    exit 1
fi

if [[ ! -s "$image_archive" ]]; then
    echo "Production image archive is missing or empty: $image_archive" >&2
    exit 1
fi

if [[ ! -s "$known_hosts_file" ]]; then
    echo "Pinned known-hosts file is missing or empty: $known_hosts_file" >&2
    exit 1
fi

if [[ ! -s "$quadlet_template" ]]; then
    echo "Quadlet template is missing or empty: $quadlet_template" >&2
    exit 1
fi

if [[ ! -r "$vps_deploy_script" ]]; then
    echo "VPS deployment script is not readable: $vps_deploy_script" >&2
    exit 1
fi

## PREPARE REMOTE STAGING

ssh_options=(
    -o StrictHostKeyChecking=yes
    -o "UserKnownHostsFile=$known_hosts_file"
    -o GlobalKnownHostsFile=/dev/null
    -o BatchMode=yes
)

staging_dir=""

# Attempt staging cleanup without replacing the deployment's exit status.
cleanup() {
    local status=$?
    trap - EXIT

    if [[ -n "$staging_dir" ]]; then
        # Substitute the validated staging path locally.
        # shellcheck disable=SC2029
        if ! ssh "${ssh_options[@]}" "$host" \
            "rm -f -- '$staging_dir/container-image.tar' '$staging_dir/theodorblom.container.in' \
             && rmdir -- '$staging_dir'"; then
            echo "Warning: remote staging cleanup failed" >&2
        fi
    fi

    exit "$status"
}
trap cleanup EXIT

remote_dir=$(ssh "${ssh_options[@]}" "$host" \
    'mktemp -d /home/github/theodorblom-deploy.XXXXXXXX')

# Only validated paths may enter remote commands, including the cleanup trap.
if [[ ! "$remote_dir" =~ ^/home/github/theodorblom-deploy\.[[:alnum:]]+$ ]]; then
    echo "Unexpected remote staging directory: $remote_dir" >&2
    exit 1
fi
staging_dir="$remote_dir"

## TRANSFER DEPLOYMENT FILES

scp "${ssh_options[@]}" "$image_archive" \
    "$host:$staging_dir/container-image.tar"
scp "${ssh_options[@]}" "$quadlet_template" \
    "$host:$staging_dir/theodorblom.container.in"

## RUN DEPLOYMENT ON VPS

# Substitute validated arguments locally; resolve the user runtime on the VPS.
# shellcheck disable=SC2029
ssh "${ssh_options[@]}" "$host" \
    "export XDG_RUNTIME_DIR=\"/run/user/\$(id -u)\";
     export DBUS_SESSION_BUS_ADDRESS=\"unix:path=\$XDG_RUNTIME_DIR/bus\";
     exec bash -s -- '$deploy_sha' '$staging_dir'" \
    <"$vps_deploy_script"
