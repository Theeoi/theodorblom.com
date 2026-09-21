import json
import os
import subprocess
import sys
import textwrap

import pytest


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
    # Use the runner's reader interface, with a different live config in cwd.
    extraction = subprocess.run(
        [sys.executable, candidate, "--print-version"],
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
with open(os.environ['LOG'], 'a') as log:
    log.write(name + ' ' + ' '.join(args) + '\\n')
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
    for name in ["git", "uv", "sudo"] + ([] if scenario == "missing" else ["sass"]):
        executable = commands / name
        executable.write_text(fake)
        executable.chmod(0o755)
    if scenario != "missing-python":
        (commands / "python3").symlink_to(sys.executable)
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
            if scenario == "missing-python":
                assert "python3: command not found" in result.stderr
                assert "sass --version" not in calls
            elif scenario not in ("no-source", "empty-source"):
                assert "expected 1.104.0; actual" in result.stderr


@pytest.mark.parametrize(
    "scenario", ["success", "invalid-sha", "version-failure", "ssh-failure"]
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
import json, os, pathlib, sys
name = pathlib.Path(sys.argv[0]).name
with open(os.environ['LOG'], 'a') as log:
    log.write(json.dumps({{'name': name, 'args': sys.argv[1:],
                          'stdin': sys.stdin.read() if name == 'ssh' else None}}) + '\\n')
if name == 'uv':
    if os.environ['SCENARIO'] == 'version-failure':
        sys.exit(1)
    print('1.104.0')
elif os.environ['SCENARIO'] == 'ssh-failure':
    sys.exit(255)
""".format(python=sys.executable)
    for name in ["uv", "ssh"]:
        executable = commands / name
        executable.write_text(fake)
        executable.chmod(0o755)
    known_hosts = tmp_path / "deploy_known_hosts"
    known_hosts.write_text("test host key\n")
    sha = "invalid;sha" if scenario == "invalid-sha" else "a" * 40
    result = subprocess.run(
        ["/bin/bash", "-c", runner],
        cwd=root,
        env=dict(
            os.environ,
            PATH=str(commands) + os.pathsep + os.environ["PATH"],
            LOG=str(log), SCENARIO=scenario, DEPLOY_SHA=sha,
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
    if scenario == "invalid-sha":
        assert calls == []
        return
    assert calls[0] == {
        "name": "uv",
        "args": ["run", "--locked", "scripts/compile_sass.py", "--print-version"],
        "stdin": None,
    }
    if scenario == "version-failure":
        assert len(calls) == 1
        return
    assert len(calls) == 2
    assert calls[1] == {
        "name": "ssh",
        "args": [
            "-o", "StrictHostKeyChecking=yes",
            "-o", "UserKnownHostsFile=" + str(known_hosts),
            "-o", "GlobalKnownHostsFile=/dev/null",
            "-o", "BatchMode=yes",
            "github@theodorblom.com", "bash -s -- " + sha + " 1.104.0",
        ],
        "stdin": (root / "scripts/deploy.sh").read_text(),
    }
