def test_deployment_uses_pinned_host_trust(pytestconfig):
    deploy = (
        pytestconfig.rootpath / ".github/workflows/deploy.yml"
    ).read_text()
    caller = (pytestconfig.rootpath / ".github/workflows/test.yml").read_text()

    deploy = " ".join(deploy.split())
    caller = " ".join(caller.split())
    host_mapping = "DEPLOY_KNOWN_HOSTS: ${{ secrets.DEPLOY_KNOWN_HOSTS }}"

    assert "DEPLOY_KNOWN_HOSTS: required: true" in deploy
    assert host_mapping in caller
    assert host_mapping in deploy
    assert "-o StrictHostKeyChecking=yes" in deploy
    assert '-o UserKnownHostsFile="$RUNNER_TEMP/deploy_known_hosts"' in deploy
    assert "-o GlobalKnownHostsFile=/dev/null" in deploy
    assert "-o BatchMode=yes" in deploy
