"""Check deployment configuration contracts, not runtime SSH behavior."""

import re
import shlex


def test_deploy_requires_and_receives_host_trust(pytestconfig):
    workflow = (pytestconfig.rootpath / ".github/workflows/deploy.yml").read_text()
    caller = (pytestconfig.rootpath / ".github/workflows/test.yml").read_text()
    assert re.search(r"DEPLOY_KNOWN_HOSTS:\s+required:\s+true\b", workflow)
    mapping = "DEPLOY_KNOWN_HOSTS: ${{ secrets.DEPLOY_KNOWN_HOSTS }}"
    assert mapping in " ".join(caller.split())
    environments = re.findall(
        r"(?m)^([ \t]*)env:[ \t]*\n((?:\1[ \t]+[^\n]*\n)+)", workflow
    )
    assert any(mapping in " ".join(block.split()) for _, block in environments)


def test_deploy_requires_pinned_host_verification(pytestconfig):
    workflow = (pytestconfig.rootpath / ".github/workflows/deploy.yml").read_text()
    command = next(
        line.strip() for line in workflow.replace("\\\n", " ").splitlines()
        if line.strip().startswith("ssh ")
    )
    arguments = shlex.split(command)
    options = dict(
        arguments[index + 1].split("=", 1)
        for index, argument in enumerate(arguments) if argument == "-o"
    )
    assert options["StrictHostKeyChecking"] == "yes"
    assert options["UserKnownHostsFile"] not in ("", "none", "/dev/null")
    assert options["GlobalKnownHostsFile"] == "/dev/null"
    assert options["BatchMode"] == "yes"
