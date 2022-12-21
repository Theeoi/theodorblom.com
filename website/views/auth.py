#!/usr/bin/env python
"""Views for the /auth url."""

from flask import Blueprint, redirect, render_template, url_for

auth = Blueprint('auth', __name__, url_prefix='/auth')


@auth.route('/login/', methods=['GET', 'POST'])
def login():
    """Definition of the /auth/login site."""
    return render_template("auth/login.html")


@auth.route('/logout/')
def logout():
    """Definition of the /auth/logout site."""
    return redirect(url_for("home.welcome"))
