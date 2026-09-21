"""Exercise deployment trust-file setup without connecting to a server."""

import os
from pathlib import Path
import subprocess
import textwrap

import pytest


@pytest.fixture
def workflow(pytestconfig):
    return (pytestconfig.rootpath / ".github/workflows/deploy.yml").read_text()


@pytest.fixture
def host_key(tmp_path):
    key = tmp_path / "server"
    subprocess.run(
        ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)],
        check=True,
    )
    return key.with_suffix(".pub").read_text()


def install_trust(workflow, tmp_path, secret):
    # Execute the workflow's setup block rather than maintaining a shell copy.
    setup = workflow.split("        run: |\n", 1)[1].split("\n      - name:", 1)[0]
    env_file = tmp_path / "github-env"
    env_file.write_text("")
    env = dict(os.environ, RUNNER_TEMP=str(tmp_path), GITHUB_ENV=str(env_file))
    env.pop("DEPLOY_KNOWN_HOSTS", None)
    if secret is not None:
        env["DEPLOY_KNOWN_HOSTS"] = secret
    result = subprocess.run(
        ["bash", "-c", textwrap.dedent(setup)],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    published = env_file.read_text().strip()
    return result, Path(published.split("=", 1)[1]) if published else None


@pytest.mark.parametrize("secret", [None, "", " \n# comment", "not a host key"])
def test_invalid_trust_blocks_setup(workflow, tmp_path, secret):
    result, path = install_trust(workflow, tmp_path, secret)
    assert result.returncode != 0
    assert "DEPLOY_KNOWN_HOSTS" in result.stdout + result.stderr
    assert path is None


def test_valid_trust_is_private_and_malformed_extra_line_fails(
    workflow, tmp_path, host_key
):
    entry = "theodorblom.com " + host_key
    result, path = install_trust(workflow, tmp_path, entry)
    assert result.returncode == 0, result.stderr
    assert path.read_text() == entry + "\n"
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.parent.stat().st_mode & 0o777 == 0o700
    result, path = install_trust(workflow, tmp_path, entry + "malformed\n")
    assert result.returncode != 0
    assert "malformed host key entry" in result.stdout
    assert path is None


def test_unrelated_host_blocks_setup(workflow, tmp_path, host_key):
    entry = "unrelated.invalid " + host_key
    result, path = install_trust(workflow, tmp_path, entry)
    assert result.returncode != 0
    assert "verified host key for theodorblom.com" in result.stdout
    assert path is None


def test_workflow_requires_and_forwards_host_trust(workflow, pytestconfig):
    caller = (pytestconfig.rootpath / ".github/workflows/test.yml").read_text()
    assert "      DEPLOY_KNOWN_HOSTS:\n        required: true" in workflow
    assert (
        "      DEPLOY_KNOWN_HOSTS: ${{ secrets.DEPLOY_KNOWN_HOSTS }}" in caller
    )
