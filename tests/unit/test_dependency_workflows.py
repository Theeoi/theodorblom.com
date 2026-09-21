#!/usr/bin/env python

import subprocess

import pytest


def test_ci_uses_locked_development_dependencies(pytestconfig):
    workflow = (pytestconfig.rootpath / ".github/workflows/test.yml").read_text()

    assert 'python-version: "3.8"' in workflow
    assert "uses: astral-sh/setup-uv@v7" in workflow
    assert "uv run --locked --extra dev pytest --cov-report=xml" in workflow
    assert "pip install" not in workflow
    assert "needs: [test, assets]" in workflow
    assert "if: github.event_name == 'push' && github.ref == 'refs/heads/main'" in workflow


def test_deployment_keeps_locked_deploy_extra_until_restart(pytestconfig):
    workflow = (pytestconfig.rootpath / ".github/workflows/deploy.yml").read_text()
    commands = [line.strip() for line in workflow.splitlines()]
    sync = commands.index("uv sync --locked --extra deploy")

    build = commands.index("uv run --locked --extra deploy scripts/compile_sass.py")
    restart = commands.index("sudo systemctl restart gunicorn-theodorblom")
    assert sync < build < restart
    assert commands.index("set -euo pipefail") < sync
    assert commands.index('git reset --hard "$deploy_sha"') < sync
    assert 'if [ "$(git rev-parse FETCH_HEAD)" != "$deploy_sha" ]; then' in commands
    assert "cancel-in-progress: false" in commands
    assert "--frozen" not in workflow


@pytest.mark.parametrize("failure", ["sync", "run", "none"])
def test_deployment_stops_before_restart_on_failure(pytestconfig, tmp_path, failure):
    workflow = (pytestconfig.rootpath / ".github/workflows/deploy.yml").read_text()
    commands = [line.strip() for line in workflow.splitlines()]
    sync = commands.index("uv sync --locked --extra deploy")
    restart = commands.index("sudo systemctl restart gunicorn-theodorblom")
    # Execute only environment preparation through restart, never SSH or checkout.
    script = "\n".join([
        commands[commands.index("set -euo pipefail")],
        *commands[sync:restart + 1],
    ])
    log = tmp_path / "commands.log"
    for name in ("git", "uv", "sudo"):
        executable = tmp_path / name
        executable.write_text(
            '#!/bin/sh\n'
            'printf "%s %s\\n" "${0##*/}" "$*" >> "$COMMAND_LOG"\n'
            'if [ "${0##*/}" = uv ] && [ "$1" = "$FAILURE" ]; then\n'
            '    exit 42\n'
            'fi\n'
            'exit 0\n'
        )
        executable.chmod(0o755)

    result = subprocess.run(
        ["/bin/bash", "-c", script],
        cwd=tmp_path,
        env={"PATH": str(tmp_path), "COMMAND_LOG": str(log), "FAILURE": failure},
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == (0 if failure == "none" else 42), result.stderr
    executed = log.read_text().splitlines()
    assert executed[0] == commands[sync]
    if failure == "sync":
        assert executed == [commands[sync]]
    elif failure == "run":
        assert executed[-1] == "uv run --locked --extra deploy scripts/compile_sass.py"
    else:
        assert executed[-1] == commands[restart]
    if failure != "none":
        assert not any(command.startswith("sudo ") for command in executed)
