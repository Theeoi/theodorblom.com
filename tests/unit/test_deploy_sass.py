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
    """Execute the workflow's remote shell, faking only external commands."""
    root = pytestconfig.rootpath
    workflow = (root / ".github/workflows/deploy.yml").read_text()
    remote = textwrap.dedent(
        workflow.split("<< 'EOF'\n", 1)[1].split("          EOF", 1)[0]
    )
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
