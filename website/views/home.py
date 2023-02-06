#!/usr/bin/env python
"""Views for the / url."""

from flask_login import current_user
from flask import Blueprint, render_template, send_from_directory, request

home = Blueprint('home', __name__, url_prefix='', static_folder='../static')


@home.route('/')
def index():
    """Definition of the / site."""
    return render_template("index.html", user=current_user)


@home.route('/robots.txt')
@home.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(home.static_folder, request.path[1:])
