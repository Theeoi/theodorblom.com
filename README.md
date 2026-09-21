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
Default development settings are found in 'src/app/config.py'. Development must
be selected explicitly; `create_app()` defaults to production.

1. Clone the repo `git clone https://github.com/Theeoi/theodorblom.com`
2. Go into the directory `cd theodorblom.com`
3. Create a Python 3.8 virtual environment `python3.8 -m venv .venv`
4. Activate the venv and install requirements `pip install .[dev]`
5. Run the app `flask --app 'app:create_app(mode="development")' run`
6. View the webpage at [127.0.0.1:5000](http://127.0.0.1:5000)

Please note:
To create an account to store in the database, remove the `@login_required` on
the create_user route. Remember to revert the changes after storing the user in
the database.

### Production Configuration

The production factory requires a readable `config.py` in Flask's instance
directory. Set `SECRET_KEY` there to a private, randomly generated string or
bytes value. Missing, empty, whitespace-only, non-string/bytes values and the
development key `secret_dev` are rejected. Keep the existing production key;
this change does not require key rotation. `DEBUG` and `TESTING` must be false.
Configuration is validated before database initialization or table creation.
Startup errors omit configuration exception details to avoid leaking secrets.

The instance directory and SQLite database paths are unchanged. Ensure the
service account can read `config.py` and access the existing database files and
their writable directory. Keep the secret configuration out of version control
and restrict access to the service account and administrators. Gunicorn and the
application dependencies must already be installed in the service environment.

The user-supplied service definition runs the factory directly, not
`scripts/wsgi.py`. It has not been independently verified on the server:

```ini
[Service]
User=github
Group=github
WorkingDirectory=/usr/share/nginx/theodorblom.com
ExecStart=/usr/bin/uv run gunicorn -w 2 -b 127.0.0.1:8000 'app:create_app()'
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
```

Service output and startup failures go to the systemd journal; inspect them with
`journalctl -u <service-name>`. This factory-based deployment does not configure
the legacy file logger in `scripts/wsgi.py`.

With `Restart=always` and `RestartSec=5`, invalid production configuration can
cause a startup retry loop (subject to systemd start limits). Before release,
obtain operator confirmation of the active service definition, expected instance
config path, valid secret and disabled debug/testing flags, and file/database
permissions for `github:github`. Release/deployment requires explicit approval;
the service definition above is not evidence that these prerequisites are met.

[#90](https://github.com/Theeoi/theodorblom.com/issues/90) proposes `--no-sync`
startup separately. The service block above retains the user-supplied command;
this configuration change does not implement that dependency-management change.
`scripts/wsgi.py` remains present because external consumers are unverified, and
its no-argument factory call is protected by the same production defaults.

For local development, instance configuration is optional and overrides the
development defaults when present. Tests must use
`create_app(test_config, mode="testing")`, which skips the instance file entirely.
Supply isolated database URLs in `test_config`; the factory does not infer testing
mode from that mapping or from `TESTING=True`. An optional absolute
`instance_path` can isolate factory configuration tests without changing normal
instance discovery. Unknown modes and test overrides outside testing mode fail.

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
