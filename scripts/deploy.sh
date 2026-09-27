#!/usr/bin/env bash
set -euo pipefail

deploy_sha="$1"
sass_version="$2"
cd /usr/share/nginx/theodorblom.com

# A slow or rerun workflow must not roll back a newer release.
git fetch origin main
if [ "$(git rev-parse FETCH_HEAD)" != "$deploy_sha" ]; then
  echo "Skipping superseded commit $deploy_sha"
  exit 0
fi

# Read the tested checker without changing the live checkout or environment.
sass_script_source=$(git show "$deploy_sha:scripts/compile_sass.py")
test -n "$sass_script_source"
# Do not sync the live project or download an interpreter during preflight.
uv run --no-project --offline \
  python -I -c "$sass_script_source" \
  --check-installed-version "$sass_version"

# Apply the release only after preflight succeeds.
git checkout main
git reset --hard "$deploy_sha"
uv sync --locked --extra deploy
uv run --locked --extra deploy scripts/compile_sass.py
sudo systemctl restart gunicorn-theodorblom
