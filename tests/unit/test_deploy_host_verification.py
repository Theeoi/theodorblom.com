"""Check deployment host-trust wiring without running SSH."""


def test_workflow_requires_and_uses_host_trust(pytestconfig):
    workflow = (pytestconfig.rootpath / ".github/workflows/deploy.yml").read_text()
    caller = (pytestconfig.rootpath / ".github/workflows/test.yml").read_text()
    assert "      DEPLOY_KNOWN_HOSTS:\n        required: true" in workflow
    assert "      DEPLOY_KNOWN_HOSTS: ${{ secrets.DEPLOY_KNOWN_HOSTS }}" in caller

    setup = workflow.split("      - name: Install pinned SSH host keys\n", 1)[1]
    setup = setup.split("\n      - name:", 1)[0]
    assert "          DEPLOY_KNOWN_HOSTS: ${{ secrets.DEPLOY_KNOWN_HOSTS }}" in setup
    assert "umask 077" in setup
    assert (
        "printf '%s\\n' \"$DEPLOY_KNOWN_HOSTS\" > \"$RUNNER_TEMP/deploy_known_hosts\""
        in setup
    )

    deploy = workflow.split("      - name: Deploy tested commit to VPS\n", 1)[1]
    assert "        shell: bash\n" in deploy
    assert "DEPLOY_KNOWN_HOSTS" not in deploy
    assert "trap 'rm -f \"$RUNNER_TEMP/deploy_known_hosts\"' EXIT" in deploy
    command = deploy.split("          ssh \\\n", 1)[1].split("<< 'EOF'", 1)[0]
    assert "-o StrictHostKeyChecking=yes" in command
    assert '-o UserKnownHostsFile="$RUNNER_TEMP/deploy_known_hosts"' in command
    assert "-o GlobalKnownHostsFile=/dev/null" in command
    assert "-o BatchMode=yes" in command
    assert "github@theodorblom.com" in command
