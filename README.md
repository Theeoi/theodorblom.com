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

Local development uses rootless [Podman](https://podman.io/) with
[podman-compose](https://github.com/containers/podman-compose) as its Compose
provider. Python, uv, Node.js, npm, and Sass are installed inside the development
image; they are not required on the host.

Clone the repository and start the development environment:

```sh
git clone https://github.com/Theeoi/theodorblom.com
cd theodorblom.com
podman compose up --build
```

Open [127.0.0.1:5000](http://127.0.0.1:5000). Source changes are visible inside
the container, and Python changes trigger a reload. Rebuild with
`podman compose up --build` after changing dependencies or the Dockerfile.
Stop the environment with `podman compose down`.

Local databases and optional configuration are stored in `.docker-instance/`.
To customize development settings, add `.docker-instance/config.py`. This
directory persists when containers are removed. Do not use production secrets
or databases for development.

See [src/app/config.py](src/app/config.py) for default settings and
[pyproject.toml](pyproject.toml) for Python compatibility and dependencies.

Run tests in a running development container:

```sh
podman compose exec web uv run --locked --extra dev --no-sync pytest
```

Run tests in a disposable development container:

```sh
podman compose run --rm --build --no-deps web \
  uv run --locked --extra dev --no-sync pytest
```

Direct `create_app()` calls in tests require `mode="testing"`, an isolated
`test_config`, and an explicit absolute `instance_path`. Testing mode ignores
`THEODORBLOM_INSTANCE_PATH` and does not load `config.py`.

Please note:
To create an account to store in the database, remove the `@login_required` on
the create_user route. Remember to revert the changes after storing the user in
the database.

### Building Stylesheets

The development container compiles stylesheets at startup using the Sass version
declared in [pyproject.toml](pyproject.toml). The generated CSS is kept in a
temporary container filesystem rather than written to your checkout. After
editing SCSS, restart the container to recompile:

```sh
podman compose restart web
```

Refresh the browser after the container restarts to see the changes.

### Deployment Environment

Production uses rootless Podman, with Gunicorn running inside the production
image and systemd managing the container through
[Quadlet](deploy/theodorblom.container.in). Nginx and Certbot remain on the VPS,
handling HTTPS and certificate renewal.

For pushes to `main`, CI tests the application and builds the production image,
including compiled stylesheets. Deployment transfers that image over SSH, loads
it on the VPS, and restarts the Quadlet service. Dependencies and assets are not
rebuilt on the VPS.

See the [CI workflow](.github/workflows/test.yml) and
[deployment workflow](.github/workflows/deploy.yml) for implementation details.

### Production Configuration

The production Quadlet mounts `/srv/theodorblom.com/instance` on the VPS at
`/instance` inside the container. This directory contains the SQLite databases
and a private `config.py` with a randomly generated `SECRET_KEY`.
`THEODORBLOM_INSTANCE_PATH` is set to `/instance`.

Debug and testing settings must remain disabled; the application refuses to
start with missing or unsafe configuration.

Keep configuration private and outside version control. The application account needs
read access to config.py and write access to the databases and their containing
directory.

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

## Contact

This code is written and maintained by [@theodorblom](https://www.theodorblom.com).
