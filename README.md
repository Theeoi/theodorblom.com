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
3. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
4. Install Python 3.8 and the locked development environment:
   `uv python install 3.8` then `uv sync --locked --extra dev`.
5. Run the app `uv run --locked --extra dev flask run`
6. View the webpage at [127.0.0.1:5000](http://127.0.0.1:5000)

The project requires Python 3.8 (`>=3.8,<3.9`); uv selects a compatible
interpreter automatically. Run the same test command as CI:

```sh
uv run --locked --extra dev pytest --cov-report=xml
```

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

### Deployment Environment

Deployment prepares the environment and builds assets before restarting the
service. Both commands validate the committed lockfile without updating it,
and both select the deployment extra so the Sass build retains Gunicorn:

```sh
uv sync --locked --extra deploy
uv run --locked --extra deploy scripts/compile_sass.py
```

If project metadata and `uv.lock` disagree, deployment must fail before the
service restart. Do not regenerate the lockfile on the server or replace
`--locked` with `--frozen`, which skips the metadata consistency check.

The supplied `gunicorn-theodorblom` systemd service currently starts with
`/usr/bin/uv run gunicorn -w 2 -b 127.0.0.1:8000 'app:create_app()'`.
The proposed service configuration is:

```ini
[Service]
User=github
Group=github
WorkingDirectory=/usr/share/nginx/theodorblom.com
ExecStart=/usr/bin/uv run --no-sync gunicorn -w 2 -b 127.0.0.1:8000 'app:create_app()'
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
```

Only `ExecStart` changes: deployment owns environment preparation; startup must
use that prepared environment without synchronizing dependencies or changing
the lockfile. `--no-sync` does not validate freshness, so it is not a substitute
for the locked deployment commands. Applying this service change and reloading
systemd require separate authorization; this repository change does not modify
the live service. Until then, the existing startup command can still
synchronize the environment without the deployment extra.

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
