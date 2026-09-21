# theodorblom.com

![Run Pytest](https://github.com/Theeoi/theodorblom.com/actions/workflows/test.yml/badge.svg?label=Tests)
![Coverage Status](https://coveralls.io/repos/github/Theeoi/theodorblom.com/badge.svg?branch=main)

A personal website deployed as a Flask app instance on a VPS.

## General Information

I believe everyone should have a personal website and decided it would be more
fun to build it from scratch than use one of the many hosting services. The
goal of the website is to act as a mix of CV, portfolio and a creative hub.

### Technologies

- Python =3.8
- Flask >=3.0

### Features

- A welcome page with links to my socials.
- A sticky mobile-friendly navbar.
- An animated favicon.
- A blogging module with Markdown-support.
- A user authentication system for admin access.
- Basic logging of website activity including hit statistics.
- A full testing suite with Pytest.
- More features coming. See [Project Status](#project-status)

## Setup

Setup is not required unless you want to explore the dev branch and/or
[contribute](#contributing).

### Usage

1. Go to [www.theodorblom.com](https://www.theodorblom.com) and enjoy!

### Contributing

If you found an error or have suggestions for further development, please
submit an issue! <3

To contribute you have to set up your own instance of the app. Settings for
your instance are made in the 'config.py' file in the 'instance' directory.
Default development settings are found in 'src/app/config.py'.

1. Clone the repo `git clone https://github.com/Theeoi/theodorblom.com`
2. Go into the directory `cd theodorblom.com`
3. Create a Python 3.8 virtual environment `python3.8 -m venv .venv`
4. Activate the venv and install requirements `pip install .[dev]`
5. Run the app `flask run`
6. View the webpage at [127.0.0.1:5000](http://127.0.0.1:5000)

Please note:
To create an account to store in the database, remove the `@login_required` on
the create_user route. Remember to revert the changes after storing the user in
the database.

### Building Stylesheets

Install the Sass CLI and ensure `sass` is on `PATH`. Sass 1.104.0 is the
version tested for this project. With Node.js and npm installed, run:

```sh
npm install --global sass@1.104.0
```

From the repository root, build the stylesheets with:

```sh
uv run --locked scripts/compile_sass.py
```

### Deployment Host Trust

Production deployment requires both repository Actions secrets `DEPLOY_KEY`
(client authentication) and `DEPLOY_KNOWN_HOSTS` (server identity). The reusable
workflow receives both from `test.yml`. The deployment step writes the host-key
secret to an owner-only temporary known-hosts file and removes it on exit,
without a separate installation or validation step. SSH requires a usable
trusted key matching `theodorblom.com`; missing or empty trust and unknown or
changed server keys block deployment before remote commands run. Malformed
extra entries do not necessarily block deployment if a usable matching key
exists. Existing runner/global host trust is not used.

Provision `DEPLOY_KNOWN_HOSTS` with OpenSSH `known_hosts` entries, for example
`theodorblom.com ssh-ed25519 <base64-public-host-key>`, one key per line. Hashed
hostnames are also supported. Obtain the host public key and its SHA256
fingerprint through an independently trusted channel, such as the provider's
authenticated console or an administrator using an already verified connection.
An authorized administrator can inspect `/etc/ssh/ssh_host_ed25519_key.pub` and
run `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` on the server. Compare the
fingerprint with the proposed entry using `ssh-keygen -lf <known-hosts-file>`
before setting the secret. Never upload the server's private host key, and never
trust unverified `ssh-keyscan` output or learn trust during deployment.

For planned host-key rotation, independently verify the new key and add its
entry alongside the old key in the secret before the server switches keys.
After the switch is verified, remove the retired entry. For an unexpected
mismatch, stop and investigate through the trusted channel rather than disabling
strict checking or blindly replacing the pin. Configure and verify the secret
before releasing this workflow to `main`; missing trust intentionally prevents
release deployment. No systemd service changes are required.

## Project Status

The website is up but is being developed sporadically.

### Roadmap

Todo:

- [x] Create a login system for admin access
- [x] Build a blog
- [x] Implement a statistics page
- [ ] Add request filtering to the stats page
- [ ] Add blogpost filtering based on tags
- [ ] Implement a FTP for file transfers (Useful for hosting blog images).

Room for improvement:

- Improve logging
- Improve the stats page

## Contact

This code is written and maintained by [@theodorblom](https://www.theodorblom.com).
