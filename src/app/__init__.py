#!/usr/bin/env python

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


def create_app(test_config=None, *, mode="production"):
    """Create the app in production, development, or explicit testing mode."""
    app = Flask(
        __name__,
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
