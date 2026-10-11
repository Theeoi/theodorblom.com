import os
from pathlib import Path

from flask import Flask
from flask_migrate import Migrate
from flask_sitemap import Sitemap
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import STATIC_FOLDER, TEMPLATE_FOLDER, load_configs
from app.database import create_dbs, db, init_db
from auth import init_login_manager
from stats import init_statistics
from website.views import register_blueprints

ext = Sitemap()
migrate = Migrate()


def create_app(
    test_config: dict[str, object] | None = None,
    *,
    mode: str = "production",
    instance_path: str | None = None,
) -> Flask:
    """Create the app in production, development, or explicit testing mode."""
    if mode not in ("production", "development", "testing"):
        raise ValueError("Unknown application mode.")

    if mode == "testing":
        default_instance_path = None
    else:
        default_instance_path = os.environ.get(
            "THEODORBLOM_INSTANCE_PATH",
            str(Path(__file__).resolve().parents[2] / "instance"),
        )

    resolved_instance_path = (
        instance_path if instance_path is not None else default_instance_path
    )

    if resolved_instance_path is None:
        raise ValueError("Testing mode requires an explicit instance_path.")
    if (
        not resolved_instance_path
        or not Path(resolved_instance_path).is_absolute()
    ):
        raise ValueError("instance_path must be a nonempty absolute path.")

    app = Flask(
        __name__,
        instance_path=resolved_instance_path,
        instance_relative_config=True,
        template_folder=TEMPLATE_FOLDER,
        static_folder=STATIC_FOLDER,
    )
    app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
    )

    load_configs(app, test_config, mode)
    init_db(app)
    ext.init_app(app)

    register_blueprints(app)

    create_dbs(app)
    migrate.init_app(app, db)

    init_statistics(app, db)

    init_login_manager(app)

    return app
