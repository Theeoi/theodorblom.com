#!/usr/bin/env python
"""Views for the /blog url."""

from flask import Blueprint, render_template
from flask_login import current_user

home = Blueprint('home', __name__, url_prefix='')


@home.route('/')
def welcome():
    """Definition of the / site."""
    return render_template("index.html", user=current_user)
