"""Exercise workflow shell and OpenSSH locally, never the deployment payload."""

import os
from pathlib import Path
import shlex
import shutil
import subprocess
import textwrap

import pytest


def unavailable(reason):
    if os.environ.get("GITHUB_ACTIONS") == "true":
        pytest.fail(reason)
    pytest.skip(reason)


@pytest.mark.parametrize("ci", [False, True])
def test_missing_prerequisite_policy(monkeypatch, ci):
    monkeypatch.setenv("GITHUB_ACTIONS", "true" if ci else "false")
    outcome = pytest.fail.Exception if ci else pytest.skip.Exception
    with pytest.raises(outcome, match="SSH prerequisite unavailable"):
        unavailable("SSH prerequisite unavailable")


@pytest.fixture
def workflow(pytestconfig):
    for tool in ("bash", "ssh", "ssh-keygen"):
        if not shutil.which(tool):
            unavailable("OpenSSH workflow tests require " + tool)
    return (pytestconfig.rootpath / ".github/workflows/deploy.yml").read_text()


@pytest.fixture
def host_keys(tmp_path):
    keys = []
    if not shutil.which("ssh-keygen"):
        unavailable("Host-key tests require ssh-keygen")
    for name in ("server", "other"):
        key = tmp_path / name
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)],
            check=True,
        )
        keys.append(key)
    return keys


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
    workflow, tmp_path, host_keys
):
    entry = "theodorblom.com " + host_keys[0].with_suffix(".pub").read_text()
    result, path = install_trust(workflow, tmp_path, entry)
    assert result.returncode == 0, result.stderr
    assert path.read_text() == entry + "\n"
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.parent.stat().st_mode & 0o777 == 0o700
    result, path = install_trust(workflow, tmp_path, entry + "malformed\n")
    assert result.returncode != 0
    assert "malformed host key entry" in result.stdout
    assert path is None


def test_unrelated_host_blocks_setup(workflow, tmp_path, host_keys):
    entry = "unrelated.invalid " + host_keys[0].with_suffix(".pub").read_text()
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


@pytest.mark.parametrize(
    "trust", ["matching", "hashed", "rotation", "unknown", "changed"]
)
def test_openssh_host_verification(workflow, tmp_path, host_keys, trust):
    sshd = shutil.which("sshd")
    if not sshd:
        unavailable("Isolated host verification requires sshd")
    config = tmp_path / "sshd_config"
    config.write_text(
        "HostKey {}\nUsePAM no\nPasswordAuthentication no\n"
        "KbdInteractiveAuthentication no\nPubkeyAuthentication no\n"
        "StrictModes yes\n".format(host_keys[0])
    )
    preflight = subprocess.run(
        [sshd, "-t", "-f", str(config)],
        capture_output=True,
        text=True,
    )
    if preflight.returncode:
        unavailable("Local sshd preflight failed: " + preflight.stderr)
    key = host_keys[1] if trust == "changed" else host_keys[0]
    entry = "theodorblom.com " + key.with_suffix(".pub").read_text()
    if trust == "hashed":
        source = tmp_path / "hashed_source"
        source.write_text(entry)
        subprocess.run(
            ["ssh-keygen", "-H", "-f", str(source)],
            check=True,
            capture_output=True,
        )
        entry = source.read_text()
    elif trust == "rotation":
        old_entry = "theodorblom.com " + host_keys[1].with_suffix(".pub").read_text()
        entry = old_entry + entry
    result, path = install_trust(workflow, tmp_path, entry)
    assert result.returncode == 0, result.stderr
    if trust == "unknown":
        path.write_text("")

    # Inetd mode runs over stdio via ProxyCommand: no listening socket or DNS.
    # Authentication is disabled so a matching pin reaches (only) auth failure.
    ssh_line = next(
        line.strip()
        for line in workflow.splitlines()
        if line.strip().startswith("ssh ")
    )
    options = shlex.split(ssh_line.split(" github@", 1)[0])[1:]
    options = [
        option.replace("$DEPLOY_KNOWN_HOSTS_FILE", str(path)) for option in options
    ]
    proxy_command = shlex.join([sshd, "-i", "-e", "-f", str(config)])
    result = subprocess.run(
        [
            "ssh", "-F", "/dev/null", "-v",
            "-o", "ProxyCommand=" + proxy_command,
            *options, "github@theodorblom.com", "false",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0
    if trust in ("matching", "hashed", "rotation"):
        assert "is known and matches" in result.stderr
        assert "Permission denied" in result.stderr
        assert "Host key verification failed" not in result.stderr
    else:
        assert "Host key verification failed" in result.stderr
        assert "Permission denied" not in result.stderr
        if trust == "changed":
            assert "REMOTE HOST IDENTIFICATION HAS CHANGED" in result.stderr
