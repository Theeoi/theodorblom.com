#!/usr/bin/env python
"""Views for the /auth url."""

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.database import db
from app.database.models import User

auth = Blueprint("auth", __name__, url_prefix="/auth")


@auth.route("/login", methods=["GET", "POST"])
def login():
    """Definition of the /auth/login site."""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                flash("Logged in!", category="success")
                login_user(user, remember=True)
                current_app.logger.info(f"User {user.username} logged in.")
                return redirect(url_for("home.index"))
            else:
                flash("Password is incorrect.", category="error")
                current_app.logger.warning(
                    "User {user.username} input wrong \
                                           password!"
                )
        else:
            flash("User does not exist.", category="error")
            current_app.logger.warning("Wrong username entered!")

    return render_template("pages/auth/login.html.jinja", user=current_user)


@auth.route("/logout")
@login_required
def logout():
    """Definition of the /auth/logout site."""
    flash("Logged out!", category="success")
    logout_user()
    current_app.logger.info(f"User {current_user} logged out.")
    return redirect(url_for("home.index"))


@auth.get("/user-admin")
@login_required
def user_admin():
    """Definition of the /auth/user-admin site."""
    users = User.query.all()
    return render_template(
        "pages/auth/user-admin.html.jinja", user=current_user, users=users
    )


@auth.post("/user-admin")
@login_required
def create_user():
    """Definition of the /auth/create-user site."""
    username = request.form.get("username")
    password1 = request.form.get("password1")
    password2 = request.form.get("password2")

    username_exists = User.query.filter_by(username=username).first()

    if username_exists:
        flash("Username already exists.", category="error")
        current_app.logger.warning("Attempted to create duplicate user!")
    elif password1 != password2:
        flash("Passwords do not match.", category="error")
        current_app.logger.warning("Password mismatch in user creation!")
    elif len(username) < 2:
        flash(
            "Username is too short. Must be at least 2 characters long.",
            category="error",
        )
        current_app.logger.warning("Created username is invalid!")
    elif len(password1) < 6:
        flash(
            "Password is too short. Must be at least 6 characters long.",
            category="error",
        )
        current_app.logger.warning("Created password is invalid!")
    else:
        new_user = User(
            username=username,
            password=generate_password_hash(password1, method="scrypt"),
        )
        db.session.add(new_user)
        db.session.commit()
        flash("User created!", category="success")
        current_app.logger.info(
            "User with username {new_user.username} \
                                was created."
        )

    return redirect(url_for("auth.user_admin"))


@auth.delete("/user-admin/<int:user_id>")
@login_required
def delete_user(user_id):
    """Definition of the /auth/create-user site."""
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash("Forbidden to delete yourself!", category="error")
        return redirect(url_for("auth.user_admin")), 303  # force redirect to GET
    db.session.delete(user)
    db.session.commit()
    flash(f"Deleted user '{user.username}'", category="success")

    return redirect(url_for("auth.user_admin")), 303  # force redirect to GET
