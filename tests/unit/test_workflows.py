def test_workflows_prepare_locked_dependencies_before_restart(pytestconfig):
    workflows = pytestconfig.rootpath / ".github/workflows"
    ci = (workflows / "test.yml").read_text()

    assert "uv run --locked --extra dev pytest --cov-report=xml" in ci
    assert "pip install" not in ci

    deployment = (workflows / "deploy.yml").read_text()
    commands = [line.strip() for line in deployment.splitlines()]
    strict_mode = commands.index("set -euo pipefail")
    sync = commands.index("uv sync --locked --extra deploy")
    build = commands.index("uv run --locked --extra deploy scripts/compile_sass.py")
    restart = commands.index("sudo systemctl restart gunicorn-theodorblom")

    assert strict_mode < sync < build < restart
