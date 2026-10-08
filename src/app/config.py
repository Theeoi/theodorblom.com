"""Configuration file for flask app.

Define default (dev) configuration variables here.
Production variables are configured through the instance config.
"""

from collections.abc import MutableMapping
from pathlib import Path
from typing import ClassVar, cast

from flask import Flask

# Flask app setup
TEMPLATE_FOLDER: str = "../website/templates"
STATIC_FOLDER: str = "../website/static"

# Flask_login config
LOGIN_VIEW: str = "auth.login"


class BaseConfig:
    # Databases
    SQLALCHEMY_BINDS: ClassVar[dict[str, str]] = {
        "auth": "sqlite:///auth.db",
        "blog": "sqlite:///blog.db",
    }
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///default.db"

    # Other
    SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS: bool = True
    SITEMAP_URL_SCHEME: str = "https"


class DevelopmentConfig(BaseConfig):
    SECRET_KEY: str = "secret_dev"


def load_configs(
    app: Flask, test_config: dict[str, object] | None, mode: str
) -> None:
    """Load mode-specific configuration before any database initialization."""
    config = cast(MutableMapping[str, object], app.config)

    if mode not in ("production", "development", "testing"):
        raise ValueError("Unknown application mode.")
    if test_config is not None and mode != "testing":
        raise ValueError("test_config requires mode='testing'.")
    if mode == "testing" and test_config is None:
        raise ValueError("Testing mode requires an isolated test_config.")

    if mode == "testing" and test_config is not None:
        config.update(test_config)
        app.config["TESTING"] = True
        return

    config_class = DevelopmentConfig if mode == "development" else BaseConfig
    app.config.from_object(config_class)

    try:
        _ = app.config.from_pyfile("config.py", silent=(mode == "development"))
    except Exception:  # noqa: BLE001
        # Config exceptions can contain secrets, including SyntaxError source lines.
        config_path = Path(app.instance_path) / "config.py"
        message = (
            f"Cannot load instance configuration at {config_path}; "
            "check readability and syntax."
        )
        if mode == "production":
            message = (
                "Production requires a readable, valid config.py. " + message
            )
        raise RuntimeError(message) from None

    if mode == "production":
        secret: object | None = config.get("SECRET_KEY")
        if (
            not isinstance(secret, (str, bytes))
            or not secret.strip()
            or secret
            in (
                DevelopmentConfig.SECRET_KEY,
                DevelopmentConfig.SECRET_KEY.encode(),
            )
        ):
            raise RuntimeError(
                "Production requires a nonempty, nondefault str/bytes SECRET_KEY."
            )
        if app.config["DEBUG"] or app.config["TESTING"]:
            raise RuntimeError("Production forbids DEBUG and TESTING settings.")
