import re
import shlex


def test_deploy_requires_and_receives_host_trust(pytestconfig):
    """Require host trust to be supplied to the deployment workflow."""
    workflow = (
        pytestconfig.rootpath / ".github/workflows/deploy.yml"
    ).read_text()
    caller = (pytestconfig.rootpath / ".github/workflows/test.yml").read_text()
    assert re.search(r"DEPLOY_KNOWN_HOSTS:\s+required:\s+true\b", workflow)
    mapping = "DEPLOY_KNOWN_HOSTS: ${{ secrets.DEPLOY_KNOWN_HOSTS }}"
    assert mapping in " ".join(caller.split())
    environments = re.findall(
        r"(?m)^([ \t]*)env:[ \t]*\n((?:\1[ \t]+[^\n]*\n)+)", workflow
    )
    assert any(mapping in " ".join(block.split()) for _, block in environments)


def test_deploy_requires_pinned_host_verification(pytestconfig):
    """Require explicit host trust and strict, noninteractive SSH verification."""
    workflow = (
        pytestconfig.rootpath / ".github/workflows/deploy.yml"
    ).read_text()
    command = next(
        line.strip()
        for line in workflow.replace("\\\n", " ").splitlines()
        if line.strip().startswith("ssh ")
    )
    arguments = shlex.split(command)
    options = dict(
        arguments[index + 1].split("=", 1)
        for index, argument in enumerate(arguments)
        if argument == "-o"
    )
    assert options["StrictHostKeyChecking"] == "yes"
    assert options["UserKnownHostsFile"] not in ("", "none", "/dev/null")
    assert options["GlobalKnownHostsFile"] == "/dev/null"
    assert options["BatchMode"] == "yes"


def test_workflows_prepare_locked_dependencies_before_restart(pytestconfig):
    """Require testing with uv and deployment in specified order."""
    workflows = pytestconfig.rootpath / ".github/workflows"
    ci = (workflows / "test.yml").read_text()

    assert "uv run --locked --extra dev pytest --cov-report=xml" in ci
    assert "pip install" not in ci

    deployment = (workflows / "deploy.yml").read_text()
    commands = [line.strip() for line in deployment.splitlines()]
    strict_mode = commands.index("set -euo pipefail")
    sync = commands.index("uv sync --locked --extra deploy")
    build = commands.index(
        "uv run --locked --extra deploy scripts/compile_sass.py"
    )
    restart = commands.index("sudo systemctl restart gunicorn-theodorblom")

    assert strict_mode < sync < build < restart
