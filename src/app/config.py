#!/usr/bin/env python
"""Configuration file for flask app.

Define default (dev) configuration variables here.
Production variables are configured through the instance config.
"""

from pathlib import Path

# Flask app setup
TEMPLATE_FOLDER = "../website/templates"
STATIC_FOLDER = "../website/static"

# Flask_login config
LOGIN_VIEW = "auth.login"


class BaseConfig:
    # Databases
    SQLALCHEMY_BINDS = {
        "auth": "sqlite:///auth.db",
        "blog": "sqlite:///blog.db",
    }
    SQLALCHEMY_DATABASE_URI = "sqlite:///default.db"

    # Other
    SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS = True
    SITEMAP_URL_SCHEME = "https"


class DevelopmentConfig(BaseConfig):
    SECRET_KEY = "secret_dev"


def load_configs(app, test_config, mode):
    """Load mode-specific configuration before any database initialization."""
    if mode not in ("production", "development", "testing"):
        raise ValueError("Unknown application mode.")
    if test_config is not None and mode != "testing":
        raise ValueError("test_config requires mode='testing'.")
    if mode == "testing" and test_config is None:
        raise ValueError("Testing mode requires an isolated test_config.")

    if mode == "testing":
        app.config.update(test_config)
        app.config["TESTING"] = True
        return

    config_class = DevelopmentConfig if mode == "development" else BaseConfig
    app.config.from_object(config_class)

    try:
        app.config.from_pyfile("config.py", silent=(mode == "development"))
    except Exception:
        # Config exceptions can contain secrets, including SyntaxError source lines.
        config_path = Path(app.instance_path) / "config.py"
        message = (
            f"Cannot load instance configuration at {config_path}; "
            "check readability and syntax."
        )
        if mode == "production":
            message = "Production requires a readable, valid config.py. " + message
        raise RuntimeError(message) from None

    if mode == "production":
        secret = app.config.get("SECRET_KEY")
        if (
            not isinstance(secret, (str, bytes))
            or not secret.strip()
            or secret in (
                DevelopmentConfig.SECRET_KEY,
                DevelopmentConfig.SECRET_KEY.encode(),
            )
        ):
            raise RuntimeError(
                "Production requires a nonempty, nondefault str/bytes SECRET_KEY."
            )
        if app.config["DEBUG"] or app.config["TESTING"]:
            raise RuntimeError("Production forbids DEBUG and TESTING settings.")
