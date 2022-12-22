#!/usr/bin/env python
"""Views for the /blog url."""

from flask import Blueprint, render_template
from flask_login import current_user

blog = Blueprint('blog', __name__, url_prefix='/blog')


@blog.route('/')
def home():
    """Definition of the /blog site."""
    return render_template("blog/index.html", user=current_user)
