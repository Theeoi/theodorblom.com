import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def test_deployment_uses_pinned_host_trust(
    pytestconfig: pytest.Config,
    tmp_path: Path,
) -> None:
    root: Path = pytestconfig.rootpath
    script: Path = root / "scripts/deploy-from-ci.sh"
    bash: str | None = shutil.which("bash")
    assert bash is not None

    (tmp_path / "deploy").mkdir()
    (tmp_path / "deploy/theodorblom.container.in").write_text(
        "[Container]\nImage=@IMAGE_REFERENCE@\n"
    )
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts/deploy-on-vps.sh").write_text(
        "#!/bin/bash\nexit 0\n"
    )

    archive: Path = tmp_path / "fake image.tar"
    archive.write_bytes(b"fake image archive")
    known_hosts: Path = tmp_path / "known_hosts"
    known_hosts.write_text("fake host key\n")

    bin_dir: Path = tmp_path / "bin"
    bin_dir.mkdir()
    command_log: Path = tmp_path / "commands.jsonl"
    mock_command: str = f"""#!{sys.executable}
import json
import os
import sys
from pathlib import Path

command = Path(sys.argv[0]).name
with open(os.environ["COMMAND_LOG"], "a") as log:
    log.write(json.dumps([command, *sys.argv[1:]]) + "\\n")

if command == "ssh" and sys.argv[-1].startswith("mktemp -d "):
    print("/home/github/theodorblom-deploy.ABCD1234")
"""

    for name in ("ssh", "scp"):
        executable: Path = bin_dir / name
        executable.write_text(mock_command)
        executable.chmod(0o755)

    result: subprocess.CompletedProcess[str] = subprocess.run(
        [
            bash,
            str(script),
            "a" * 40,
            str(archive),
            str(known_hosts),
        ],
        cwd=tmp_path,
        env={
            "PATH": str(bin_dir),
            "HOME": str(tmp_path),
            "COMMAND_LOG": str(command_log),
            "LC_ALL": "C",
        },
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
    calls: list[list[str]] = [
        json.loads(line) for line in command_log.read_text().splitlines()
    ]
    assert {call[0] for call in calls} == {"ssh", "scp"}

    required_options: set[str] = {
        "StrictHostKeyChecking=yes",
        f"UserKnownHostsFile={known_hosts}",
        "GlobalKnownHostsFile=/dev/null",
        "BatchMode=yes",
    }

    for command, *arguments in calls:
        options: set[str] = {
            arguments[index + 1]
            for index, argument in enumerate(arguments[:-1])
            if argument == "-o"
        }
        assert required_options <= options, (
            f"{command} omitted pinned host verification: {arguments}"
        )
