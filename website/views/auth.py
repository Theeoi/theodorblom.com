#!/usr/bin/env python
"""Views for the /auth url."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user, login_required
from .. import db
from ..models import User
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__, url_prefix='/auth')


@auth.route('/login/', methods=['GET', 'POST'])
def login():
    """Definition of the /auth/login site."""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                flash("Logged in!", category='success')
                login_user(user, remember=True)
                return redirect(url_for('home.welcome'))
            else:
                flash("Password is incorrect.", category='error')
        else:
            flash("User does not exist.", category='error')

    return render_template("auth/login.html")


@auth.route('/logout/')
@login_required
def logout():
    """Definition of the /auth/logout site."""
    flash("Logged out!", category='success')
    logout_user()
    return redirect(url_for("home.welcome"))


@auth.route('/create-user/', methods=['GET', 'POST'])
def create_user():
    """Definition of the /auth/create-user site."""
    if request.method == "POST":
        username = request.form.get("username")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        username_exists = User.query.filter_by(username=username).first()

        if username_exists:
            flash("Username already exists.", category='error')
        elif password1 != password2:
            flash("Passwords do not match.", category='error')
        elif len(username) < 2:
            flash("Username is too short. Must be at least 2 characters long.",
                  category='error')
        elif len(password1) < 6:
            flash("Password is too short. Must be at least 6 characters long.",
                  category='error')
        else:
            new_user = User(username=username,
                            password=generate_password_hash(password1,
                                                            method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            flash("User created!", category='success')

    return render_template("auth/create-user.html")
