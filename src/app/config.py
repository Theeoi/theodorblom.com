#!/usr/bin/env python
"""Configuration file for flask app.

Define default (dev) configuration variables here.
Production variables are configured through the instance config.
"""

# Flask app setup
TEMPLATE_FOLDER = "../website/templates"
STATIC_FOLDER = "../website/static"

# Flask_login config
LOGIN_VIEW = "auth.login"


class DefaultConfig:
    # Flask essentials
    SECRET_KEY = "secret_dev"

    # Databases
    SQLALCHEMY_BINDS = {
        "auth": "sqlite:///auth.db",
        "blog": "sqlite:///blog.db",
    }
    SQLALCHEMY_DATABASE_URI = "sqlite:///default.db"

    # Other
    SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS = True
    SITEMAP_URL_SCHEME = "https"


def load_configs(app, test_config):
    """Loads all configuration onto the app.

    Args:
        app (Flask): A Flask app instance.
        test_config (dict | None): Mapping of additional configuration options.
    """
    # Load default app config
    app.config.from_object("app.config.DefaultConfig")

    # Load any instance config (if it exists)
    app.config.from_pyfile("config.py", silent=True)

    # Update with supplied test-config
    if test_config is not None:
        app.config.update(test_config)
