import json
import os
import shutil
import subprocess
import sys
import textwrap

import pytest


@pytest.mark.parametrize("environment", ["existing", "absent", "no-python"])
def test_uv_preflight_leaves_project_untouched(pytestconfig, tmp_path, environment):
    """Real uv must check Sass without bootstrapping or syncing the live project."""
    uv = shutil.which("uv")
    assert uv is not None, "Run deployment tests with uv installed"
    project = tmp_path / "project"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        '[project]\nname = "preflight-test"\nversion = "0.0.0"\n'
        'requires-python = ">=3.8,<3.9"\n'
        'dependencies = ["must-not-be-installed-during-preflight"]\n'
    )
    # Neither file needs to be usable: preflight must not resolve the project.
    (project / "uv.lock").write_text("unchanged lockfile sentinel\n")
    (project / "scripts").mkdir()
    (project / "scripts/compile_sass.py").write_text(
        "raise AssertionError('live script used')\n"
    )
    if environment == "existing":
        subprocess.run(
            [sys.executable, "-m", "venv", "--without-pip", project / ".venv"],
            check=True, capture_output=True,
        )

    def snapshot():
        return {
            str(path.relative_to(project)): (
                path.lstat().st_mode,
                path.lstat().st_mtime_ns,
                os.readlink(path) if path.is_symlink() else
                path.read_bytes() if path.is_file() else None,
            )
            for path in project.rglob("*")
        }

    before = snapshot()
    commands = tmp_path / "bin"
    commands.mkdir()
    sass = commands / "sass"
    sass.write_text(f"#!{sys.executable}\nprint('1.104.0')\n")
    sass.chmod(0o755)
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith(("UV_", "PYTHON", "VIRTUAL_ENV", "CONDA"))
    }
    env.update(
        PATH=str(commands),
        HOME=str(tmp_path / "home"),
        XDG_CONFIG_HOME=str(tmp_path / "config"),
        UV_CACHE_DIR=str(tmp_path / "cache"),
        UV_PYTHON_INSTALL_DIR=str(tmp_path / "interpreters"),
    )
    if environment == "absent":
        env["UV_PYTHON"] = sys.executable
    elif environment == "no-python":
        env["UV_PYTHON_PREFERENCE"] = "only-managed"
    source = (pytestconfig.rootpath / "scripts/compile_sass.py").read_text()
    result = subprocess.run(
        [uv, "run", "--no-project", "--offline", "python", "-I", "-c",
         source, "--check-installed-version", "1.104.0"],
        cwd=project, env=env, capture_output=True, text=True,
    )
    assert snapshot() == before
    assert not list((tmp_path / "interpreters").glob("cpython-*"))
    if environment == "no-python":
        assert result.returncode != 0
        assert "offline" in result.stderr.lower(), result.stderr
    else:
        assert result.returncode == 0, result.stderr
    assert (project / ".venv").exists() == (environment == "existing")


@pytest.mark.parametrize(
    "scenario",
    [
        "match",
        "mismatch",
        "missing",
        "nonzero",
        "malformed",
        "no-source",
        "empty-source",
        "missing-uv",
        "missing-python",
        "superseded",
    ],
)
def test_remote_preflight(pytestconfig, tmp_path, scenario):
    """Execute the remote deployment script, faking only external commands."""
    root = pytestconfig.rootpath
    remote = (root / "scripts/deploy.sh").read_text()
    # Keep the actual deployment commands and ordering; redirect only its cwd.
    remote = remote.replace("/usr/share/nginx/theodorblom.com", str(tmp_path))
    candidate_root = tmp_path / "candidate"
    (candidate_root / "scripts").mkdir(parents=True)
    candidate = candidate_root / "scripts/compile_sass.py"
    candidate.write_text((root / "scripts/compile_sass.py").read_text())
    (candidate_root / "pyproject.toml").write_text(
        "[tool.sass]\nversion = '1.104.0' # Candidate version, not live version\n"
    )
    # The live tree deliberately cannot supply a working checker.
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/compile_sass.py").write_text(
        "raise AssertionError('live checker used')"
    )
    (tmp_path / "pyproject.toml").write_text('[tool.sass]\nversion = "1.103.0"\n')
    # Use the assets reader interface, with a different live config in cwd.
    extraction = subprocess.run(
        [sys.executable, candidate, "--print-configured-version"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    expected = extraction.stdout.strip()
    assert expected == "1.104.0"
    commands = tmp_path / "bin"
    commands.mkdir()
    log = tmp_path / "commands.log"
    fake = """#!{python}
import os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
logged_args = args
if name == 'uv' and '-c' in args:
    logged_args = args[:6] + ['<source>'] + args[7:]
with open(os.environ['LOG'], 'a') as log:
    log.write(name + ' ' + ' '.join(logged_args) + '\\n')
scenario = os.environ['SCENARIO']
if name == 'git':
    if args[0] == 'rev-parse':
        print('b' * 40 if scenario == 'superseded' else 'a' * 40)
    elif args[0] == 'show':
        assert args[1] == 'a' * 40 + ':scripts/compile_sass.py'
        if scenario == 'no-source':
            sys.exit(1)
        if scenario != 'empty-source':
            print(pathlib.Path(os.environ['CANDIDATE']).read_text())
elif name == 'uv' and '--no-project' in args:
    assert args[:6] == ['run', '--no-project', '--offline', 'python', '-I', '-c']
    source = pathlib.Path(os.environ['CANDIDATE']).read_text().rstrip('\\n')
    assert args[6] == source
    assert args[7:] == ['--check-installed-version', '1.104.0']
    if scenario == 'missing-python':
        print('No Python interpreter available', file=sys.stderr)
        sys.exit(2)
    os.execv(sys.executable, [sys.executable] + args[4:])
elif name == 'sass':
    if scenario == 'nonzero':
        sys.exit(2)
    if scenario == 'mismatch':
        print('1.103.0')
    elif scenario == 'malformed':
        print('broken')
    else:
        print('1.104.0 compiled with dart2js 3.11.2')
""".format(python=sys.executable)
    names = ["git", "sudo"]
    if scenario != "missing-uv":
        names.append("uv")
    if scenario != "missing":
        names.append("sass")
    for name in names:
        executable = commands / name
        executable.write_text(fake)
        executable.chmod(0o755)
    env = dict(
        os.environ,
        PATH=str(commands),
        LOG=str(log),
        SCENARIO=scenario,
        CANDIDATE=str(candidate),
    )
    result = subprocess.run(
        ["/bin/bash", "-s", "--", "a" * 40, expected],
        input=remote,
        text=True,
        capture_output=True,
        env=env,
    )
    calls = log.read_text().splitlines()
    mutations = [
        line for line in calls
        if line.startswith(("git checkout", "git reset", "uv ", "sudo "))
        and not line.startswith("uv run --no-project --offline ")
    ]
    if scenario == "match":
        assert result.returncode == 0, result.stderr
        assert len(mutations) == 5
        assert mutations[:2] == ["git checkout main", "git reset --hard " + "a" * 40]
        assert mutations[2].split()[:2] == ["uv", "sync"]
        assert mutations[3].split()[:2] == ["uv", "run"]
        assert mutations[3].split()[-1] == "scripts/compile_sass.py"
        assert mutations[4] == "sudo systemctl restart gunicorn-theodorblom"
        assert calls.index("sass --version") < calls.index("git checkout main")
    else:
        assert not mutations
        if scenario == "superseded":
            assert result.returncode == 0
            assert "Skipping superseded commit" in result.stdout
            assert len(calls) == 2
        else:
            assert result.returncode != 0
            if scenario in ("missing-uv", "missing-python"):
                message = (
                    "uv: command not found" if scenario == "missing-uv" else
                    "No Python interpreter available"
                )
                assert message in result.stderr
                assert "sass --version" not in calls
            elif scenario not in ("no-source", "empty-source"):
                assert "expected 1.104.0; actual" in result.stderr


@pytest.mark.parametrize(
    "scenario", ["success", "invalid-sha", "missing-version", "ssh-failure"]
)
def test_runner_deployment(pytestconfig, tmp_path, scenario):
    """Exercise the workflow's runner shell without connecting to the VPS."""
    root = pytestconfig.rootpath
    workflow = (root / ".github/workflows/deploy.yml").read_text()
    step = workflow.split("- name: Deploy tested commit to VPS\n", 1)[1]
    lines = step.split("run: |\n", 1)[1].splitlines()
    indentation = len(lines[0]) - len(lines[0].lstrip())
    script_lines = []
    for line in lines:
        if line.strip() and len(line) - len(line.lstrip()) < indentation:
            break
        script_lines.append(line)
    runner = textwrap.dedent("\n".join(script_lines))
    syntax = subprocess.run(
        ["/bin/bash", "-n"], input=runner, text=True, capture_output=True
    )
    assert syntax.returncode == 0, syntax.stderr

    commands = tmp_path / "bin"
    commands.mkdir()
    log = tmp_path / "commands.jsonl"
    fake = """#!{python}
import json, os, sys
with open(os.environ['LOG'], 'a') as log:
    log.write(json.dumps({{'args': sys.argv[1:],
                          'stdin': sys.stdin.read()}}) + '\\n')
if os.environ['SCENARIO'] == 'ssh-failure':
    sys.exit(255)
""".format(python=sys.executable)
    executable = commands / "ssh"
    executable.write_text(fake)
    executable.chmod(0o755)
    known_hosts = tmp_path / "deploy_known_hosts"
    host_step = workflow.split("- name: Install pinned SSH host keys\n", 1)[1]
    host_script = textwrap.dedent(
        host_step.split("run: |\n", 1)[1].split("- name: Install SSH key", 1)[0]
    )
    subprocess.run(
        ["/bin/bash", "-c", host_script],
        env=dict(os.environ, RUNNER_TEMP=str(tmp_path),
                 DEPLOY_KNOWN_HOSTS="test host key"),
        check=True,
        capture_output=True,
    )
    assert known_hosts.read_text() == "test host key\n"
    assert known_hosts.stat().st_mode & 0o777 == 0o600
    sha = "invalid;sha" if scenario == "invalid-sha" else "a" * 40
    result = subprocess.run(
        ["/bin/bash", "-c", runner],
        cwd=root,
        env=dict(
            os.environ,
            PATH=str(commands) + os.pathsep + os.environ["PATH"],
            LOG=str(log), SCENARIO=scenario, DEPLOY_SHA=sha,
            SASS_VERSION="" if scenario == "missing-version" else "1.104.0",
            RUNNER_TEMP=str(tmp_path),
        ),
        text=True,
        capture_output=True,
    )
    assert not known_hosts.exists()
    assert (result.returncode == 0) == (scenario == "success"), result.stderr
    calls = []
    if log.exists():
        calls = [json.loads(line) for line in log.read_text().splitlines()]
    if scenario in ("invalid-sha", "missing-version"):
        assert calls == []
        if scenario == "missing-version":
            assert "Missing Sass version from assets" in result.stderr
        return
    assert len(calls) == 1
    assert calls[0] == {
        "args": [
            "-o", "StrictHostKeyChecking=yes",
            "-o", "UserKnownHostsFile=" + str(known_hosts),
            "-o", "GlobalKnownHostsFile=/dev/null",
            "-o", "BatchMode=yes",
            "github@theodorblom.com", "bash -s -- " + sha + " 1.104.0",
        ],
        "stdin": (root / "scripts/deploy.sh").read_text(),
    }
