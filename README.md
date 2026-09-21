# theodorblom.com

![Run Pytest](https://github.com/Theeoi/theodorblom.com/actions/workflows/test.yml/badge.svg?label=Tests)
![Coverage Status](https://coveralls.io/repos/github/Theeoi/theodorblom.com/badge.svg?branch=main)

A personal website deployed as a Flask app instance on a VPS.

## General Information

I believe everyone should have a personal website and decided it would be more
fun to build it from scratch than use one of the many hosting services. The
goal of the website is to act as a mix of CV, portfolio and a creative hub.

### Technologies

- Python
- Flask

See [pyproject.toml](pyproject.toml) for compatibility and dependency requirements.

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
3. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
4. Install the locked development environment: `uv sync --locked --extra dev`.
5. Run the app `uv run --locked --extra dev flask run`
6. View the webpage at [127.0.0.1:5000](http://127.0.0.1:5000)

Python compatibility is defined by `requires-python` in
[pyproject.toml](pyproject.toml). With its default settings, uv selects a compatible
interpreter automatically and downloads one if needed.

Run the same test command as CI:

```sh
uv run --locked --extra dev pytest --cov-report=xml
```

Please note:
To create an account to store in the database, remove the `@login_required` on
the create_user route. Remember to revert the changes after storing the user in
the database.

### Building Stylesheets

Install the Sass CLI and ensure `sass` is on `PATH`. The required version is
declared in `[tool.sass]` in `pyproject.toml`. With Node.js, npm, and uv installed, run:

```sh
sass_version=$(uv run --locked scripts/compile_sass.py --print-version)
npm install --global "sass@$sass_version"
```

From the repository root, build the stylesheets with:

```sh
uv run --locked scripts/compile_sass.py
```

Local builds reject missing or mismatched Sass versions before compilation.
The assets workflow reads and validates the candidate's expected version, then
passes it to deployment as a reusable-workflow output. The deployment runner
does not need Python or uv; it sends `scripts/deploy.sh` to the VPS over SSH.
Deployment-only retries reuse the successful assets job's version output.
After fetching and skipping superseded releases, the server runs the candidate's
checker before changing the live checkout, dependencies, assets, or service.
The server must already have `uv` and the required Sass on its noninteractive
`PATH`, plus a Python interpreter (3.8 or newer) discoverable by uv. A standalone
`python3` command on `PATH` is not required. Preflight uses
`uv run --no-project --offline` to avoid syncing the live project or downloading
an interpreter; the check needs only the standard library, not the app or a TOML
parser. Normal locked project synchronization happens only after preflight
succeeds and still enforces the application's Python requirement. A failed check
requires manual tooling correction; preflight never installs server tooling.

### Deployment Environment

The site runs on a VPS, with Gunicorn serving the Flask application and systemd
managing the service. CI and deployment use the committed dependency lockfile
to keep Python dependencies consistent.

Updates to `main` are deployed after automated tests and asset checks pass.
Deployment prepares dependencies and stylesheets before restarting the application.

See the [CI workflow](.github/workflows/test.yml) and
[deployment workflow](.github/workflows/deploy.yml) for implementation details.

### Deployment Host Trust

Set the repository Actions secret `DEPLOY_KNOWN_HOSTS` to an independently
verified VPS public host key in `known_hosts` format:
`theodorblom.com ssh-ed25519 <base64-public-host-key>`.

For planned host-key rotation, replace the secret's value with both the existing
and independently verified new key, one entry per line, before switching the
server key. After verifying the rotation, update the secret to contain only the
new key. Investigate unexpected key mismatches rather than disabling verification.

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
