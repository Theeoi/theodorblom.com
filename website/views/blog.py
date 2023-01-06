#!/usr/bin/env python
"""Views for the /blog url."""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required

blog = Blueprint('blog', __name__, url_prefix='/blog')


# @blog.route('/')
# def home():
#     """Definition of the /blog site."""
#     return redirect(url_for("blogging.index"))
#     # return render_template("blog/index.html", user=current_user)
#
#
# @blog.route('/editor/')
# @login_required
# def create_post():
#     """Definition of the /blog/editor site."""
#     return redirect(url_for("blogging.editor"))
#     # return render_template("blog/editor.html", user=current_user)
