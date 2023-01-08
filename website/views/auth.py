#!/usr/bin/env python
"""Views for the /auth url."""

from werkzeug.security import generate_password_hash, check_password_hash
from ..models import User
from .. import db
from flask_login import login_user, logout_user, login_required, current_user
from flask import (Blueprint, flash, redirect, render_template, request,
                   url_for, current_app)

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
                current_app.logger.info(f"User {user.username} logged in.")
                return redirect(url_for('home.index'))
            else:
                flash("Password is incorrect.", category='error')
                current_app.logger.warning("User {user.username} input wrong \
                                           password!")
        else:
            flash("User does not exist.", category='error')
            current_app.logger.warning("Wrong username entered!")

    return render_template("auth/login.html", user=current_user)


@auth.route('/logout/')
@login_required
def logout():
    """Definition of the /auth/logout site."""
    flash("Logged out!", category='success')
    logout_user()
    current_app.logger.info(f"User {current_user} logged out.")
    return redirect(url_for("home.index"))


@auth.route('/create-user/', methods=['GET', 'POST'])
@login_required
def create_user():
    """Definition of the /auth/create-user site."""
    if request.method == "POST":
        username = request.form.get("username")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        username_exists = User.query.filter_by(username=username).first()

        if username_exists:
            flash("Username already exists.", category='error')
            current_app.logger.warning("Attempted to create duplicate user!")
        elif password1 != password2:
            flash("Passwords do not match.", category='error')
            current_app.logger.warning("Password mismatch in user creation!")
        elif len(username) < 2:
            flash("Username is too short. Must be at least 2 characters long.",
                  category='error')
            current_app.logger.warning("Created username is invalid!")
        elif len(password1) < 6:
            flash("Password is too short. Must be at least 6 characters long.",
                  category='error')
            current_app.logger.warning("Created password is invalid!")
        else:
            new_user = User(username=username,
                            password=generate_password_hash(password1,
                                                            method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            flash("User created!", category='success')
            current_app.logger.info("User with username {new_user.username} \
                                    was created.")

    return render_template("auth/create-user.html", user=current_user)
