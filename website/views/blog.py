#!/usr/bin/env python
"""Views for the /blog url."""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required

blog = Blueprint('blog', __name__, url_prefix='/blog')


@blog.route('/')
def home():
    """Definition of the /blog site."""
    return render_template("blog/index.html", user=current_user)


@blog.route('/create-post/')
@login_required
def create_post():
    """Definition of the /blog/create-post site."""
    return redirect(url_for('blogging.editor'))
