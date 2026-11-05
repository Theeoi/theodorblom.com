#!/usr/bin/env bash
set -euo pipefail

# skip stale workflow runs without requiring a source checkout on the VPS.
check_current_release() {
    local remote_ref
    local latest_sha

    remote_ref=$(git ls-remote --exit-code \
        https://github.com/Theeoi/theodorblom.com.git \
        refs/heads/main)

    latest_sha="${remote_ref%%$'\t'*}"

    if [[ "$latest_sha" != "$deploy_sha" ]]; then
        echo "Skipping superseded commit $deploy_sha"
        exit 0
    fi
}

## VALIDATE PREREQUISITES

deploy_sha="${1:?Missing deployment commit SHA}"
staging_dir="${2:?Missing staging directory}"
image_archive="$staging_dir/container-image.tar"
quadlet_dir="${XDG_CONFIG_HOME:-$HOME/.config}/containers/systemd"
quadlet_file="$quadlet_dir/theodorblom.container"
quadlet_template="$staging_dir/theodorblom.container.in"
lock_dir="${XDG_RUNTIME_DIR:?Missing user runtime directory}"
instance_dir="/srv/theodorblom.com/instance"

if [[ ! "$deploy_sha" =~ ^[0-9a-f]{40}$ ]]; then
    echo "Invalid deployment commit SHA" >&2
    exit 1
fi

if [[ "$staging_dir" != /* ]]; then
    echo "Staging directory must be an absolute path" >&2
    exit 1
fi

test -s "$image_archive"
test -s "$quadlet_template"

if ! grep -Fxq 'Image=@IMAGE_REFERENCE@' "$quadlet_template"; then
    echo "Quadlet template is missing its image placeholder" >&2
    exit 1
fi

# Production data is provisioned separately; never create empty storage here.
test -d "$instance_dir"
test -w "$instance_dir"

if [[ ! -r "$instance_dir/config.py" ]]; then
    echo "Production configuration is not readable: $instance_dir/config.py" >&2
    exit 1
fi

if [[ "$(podman info --format '{{.Host.Security.Rootless}}')" != true ]]; then
    echo "Deployment requires rootless Podman" >&2
    exit 1
fi

# Hold this lock until exit to serialize image tagging and service replacement.
exec 9>"$lock_dir/theodorblom-deploy.lock"
flock -x 9

check_current_release

## LOAD IMAGE AND RENDER QUADLET

# CI exports a fixed tag; give each deployed release its own commit-specific tag.
source_image="localhost/theodorblom-production:ci"
release_image="localhost/theodorblom-production:sha-$deploy_sha"

podman load --input "$image_archive"

image_id=$(podman image inspect --format '{{.Id}}' "$source_image")

podman tag "$image_id" "$release_image"

echo "Prepared image $release_image ($image_id)"

mkdir -p "$quadlet_dir"

# Render beside the destination so installation can use an atomic rename.
temporary_quadlet=$(mktemp "$quadlet_dir/.theodorblom.XXXXXX")

cleanup() {
    rm -f -- "$temporary_quadlet"
}
trap cleanup EXIT

sed "s|^Image=@IMAGE_REFERENCE@$|Image=$release_image|" \
    "$quadlet_template" >"$temporary_quadlet"

chmod 644 "$temporary_quadlet"

## INSTALL QUADLET AND RESTART SERVICE

# main branch may have advanced while the image was loading.
check_current_release

mv -f -- "$temporary_quadlet" "$quadlet_file"

# Regenerate the user service from the updated Quadlet before restarting it.
systemctl --user daemon-reload
systemctl --user restart theodorblom.service

echo "Service restart completed for $deploy_sha"
