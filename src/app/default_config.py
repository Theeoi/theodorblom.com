#!/usr/bin/env python
"""
Configuration file for flask app.

Define default (dev) configuration variables here.
Production variables are configured on the server.
"""

TEMPLATE_FOLDER = "../website/templates"
STATIC_FOLDER = "../website/static"

HOST = "0.0.0.0"
DEBUG = True
SECRET_KEY = "dev"
SQLALCHEMY_DATABASE_URI = "sqlite:///default.db"
SQLALCHEMY_BINDS = {
    "auth": "sqlite:///auth.db",
    "blog": "sqlite:///blog.db",
}
BLOGGING_URL_PREFIX = "/blog"
SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS = True
SITEMAP_URL_SCHEME = "https"
