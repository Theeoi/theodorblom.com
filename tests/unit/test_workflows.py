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

    deployment = (pytestconfig.rootpath / "scripts/deploy.sh").read_text()
    commands = [line.strip() for line in deployment.splitlines()]
    strict_mode = commands.index("set -euo pipefail")
    sync = commands.index("uv sync --locked --extra deploy")
    build = commands.index(
        "uv run --locked --extra deploy scripts/compile_sass.py"
    )
    restart = commands.index("sudo systemctl restart gunicorn-theodorblom")

    assert strict_mode < sync < build < restart


def test_assets_version_passed_to_deployment(pytestconfig):
    """Keep the validated build version wired through both reusable workflows."""
    workflows = pytestconfig.rootpath / ".github/workflows"
    assets = (workflows / "assets.yml").read_text()
    caller = (workflows / "test.yml").read_text()
    deploy = (workflows / "deploy.yml").read_text()

    assert re.search(
        r"workflow_call:\s+outputs:\s+sass_version:\s+description:[^\n]+\n"
        r"\s+value: \$\{\{ jobs.build.outputs.sass_version \}\}", assets
    )
    assert re.search(
        r"outputs:\s+sass_version: \$\{\{ steps.sass.outputs.sass_version \}\}",
        assets,
    )
    assert re.search(r"- name: Install Sass\s+id: sass\s+run: \|", assets)
    reader = assets.index(
        "sass_version=$(uv run --locked scripts/compile_sass.py --print-version)"
    )
    install = assets.index('npm install --global "sass@$sass_version"')
    publish = assets.index(
        "printf 'sass_version=%s\\n' \"$sass_version\" >> \"$GITHUB_OUTPUT\""
    )
    assert reader < install < publish
    assert re.search(
        r"deploy:\s+needs: \[test, assets\][\s\S]+?"
        r"uses: \./.github/workflows/deploy.yml\s+with:\s+"
        r"sass_version: \$\{\{ needs.assets.outputs.sass_version \}\}", caller
    )
    assert re.search(
        r"workflow_call:\s+inputs:\s+sass_version:\s+description:[^\n]+\n"
        r"\s+required: true\s+type: string", deploy
    )
    assert "SASS_VERSION: ${{ inputs.sass_version }}" in deploy
    assert "setup-python" not in deploy
    assert "setup-uv" not in deploy
    assert "--print-version" not in deploy
