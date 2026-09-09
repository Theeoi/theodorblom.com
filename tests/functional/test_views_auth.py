#!/usr/bin/env python

from conftest import ADMIN_USER
from flask_login import current_user
from markupsafe import escape
from werkzeug.security import check_password_hash

from app.database import db
from app.database.models import User

TEST_USER = {
    "username": "testingPhil",
    "password1": "philsPassword123",
    "password2": "philsPassword123",
}


class TestLogin:
    def test_login_page(self, test_client):
        response = test_client.get("auth/login")
        assert current_user.is_authenticated is False
        assert response.status_code == 200
        assert b"Login" in response.data

    def test_login_success(self, test_client, admin_user):
        response = test_client.post(
            "/auth/login", data=ADMIN_USER, follow_redirects=True
        )
        assert response.status_code == 200
        assert current_user.is_authenticated is True
        assert b"Logged in!" in response.data
        assert b"Logout" in response.data

    def test_logout(self, test_client, authenticated_user):
        assert current_user.is_authenticated is True
        response = test_client.get("/auth/logout", follow_redirects=True)
        assert response.status_code == 200
        assert current_user.is_authenticated is False
        assert b"Login" in response.data

    def test_login_wrong_password(self, test_client, admin_user):
        data = {
            "username": ADMIN_USER["username"],
            "password": "Password123",
        }
        response = test_client.post("/auth/login", data=data, follow_redirects=True)
        assert response.status_code == 200
        assert b"Password is incorrect" in response.data
        assert current_user.is_authenticated is False

    def test_login_invalid_user(self, test_client):
        response = test_client.post(
            "/auth/login", data=ADMIN_USER, follow_redirects=True
        )
        assert response.status_code == 200
        assert b"User does not exist" in response.data
        assert current_user.is_authenticated is False


class TestCreateUser:
    def test_user_admin_redirect(self, test_client):
        response = test_client.get("/auth/user-admin")
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]

    def test_create_user_success(self, test_client, authenticated_user):
        response = test_client.post(
            "/auth/user-admin", data=TEST_USER, follow_redirects=True
        )
        assert response.status_code == 200
        assert User.query.filter_by(username=TEST_USER["username"]).first() is not None

    def test_create_duplicate_user(self, test_client, authenticated_user):
        response = test_client.post(
            "/auth/user-admin", data=TEST_USER, follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Username already exists." in response.data
        assert User.query.filter_by(username=TEST_USER["username"]).first() is not None

    def test_create_user_password_mismatch(self, test_client, authenticated_user):
        data = {
            "username": "mismatchPhil",
            "password1": "philsPassword123",
            "password2": "philsPassword1234",
        }
        response = test_client.post(
            "/auth/user-admin", data=data, follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Passwords do not match." in response.data
        assert User.query.filter_by(username="mismatchPhil").first() is None

    def test_create_user_short_username(self, test_client, authenticated_user):
        data = {
            "username": "P",
            "password1": "philsPassword123",
            "password2": "philsPassword123",
        }
        response = test_client.post(
            "/auth/user-admin", data=data, follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Username is too short." in response.data
        assert User.query.filter_by(username="P").first() is None

    def test_create_user_short_password(self, test_client, authenticated_user):
        data = {"username": "shortPhil", "password1": "12345", "password2": "12345"}
        response = test_client.post(
            "/auth/user-admin", data=data, follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Password is too short." in response.data
        assert User.query.filter_by(username="shortPhil").first() is None


class TestChangeUserPwd:
    def test_change_pwd_form(self, test_client, authenticated_user):
        response = test_client.patch(
            f"/auth/user-admin/{authenticated_user.id}", follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Repeat new password" in response.data

    def test_change_user_pwd_old_mismatch(self, test_client, authenticated_user):
        data = {
            "old_password": "philsPassword1234",
            "new_password1": "philsPassword321",
            "new_password2": "philsPassword321",
        }
        response = test_client.post(
            f"/auth/user-admin/{authenticated_user.id}",
            data=data,
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Current password is incorrect." in response.data

    def test_change_user_pwd_short_password(self, test_client, authenticated_user):
        data = {
            "old_password": f"{ADMIN_USER['password']}",
            "new_password1": "12345",
            "new_password2": "12345",
        }
        response = test_client.post(
            f"/auth/user-admin/{authenticated_user.id}",
            data=data,
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Password is too short." in response.data

    def test_change_user_pwd_new_mismatch(self, test_client, authenticated_user):
        data = {
            "old_password": f"{ADMIN_USER['password']}",
            "new_password1": "philsPassword321",
            "new_password2": "philsPassword3210",
        }
        response = test_client.post(
            f"/auth/user-admin/{authenticated_user.id}",
            data=data,
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Passwords do not match." in response.data

    def test_change_user_pwd_success(self, test_client, authenticated_user):
        data = {
            "old_password": f"{ADMIN_USER['password']}",
            "new_password1": "philsPassword321",
            "new_password2": "philsPassword321",
        }
        response = test_client.post(
            f"/auth/user-admin/{authenticated_user.id}",
            data=data,
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Successfully changed password!" in response.data

    def test_change_user_pwd_unauthorized(self, test_client, admin_user):
        data = {
            "old_password": f"{ADMIN_USER['password']}",
            "new_password1": "philsPassword321",
            "new_password2": "philsPassword321",
        }
        response = test_client.post(f"/auth/user-admin/{admin_user.id}", data=data)
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]
        assert check_password_hash(admin_user.password, ADMIN_USER["password"])


class TestDeleteUser:
    def test_username_is_escaped(self, test_client, authenticated_user):
        authenticated_user.username = '<b title="user">Name & \'quotes\'</b>'
        db.session.commit()

        response = test_client.get("/auth/user-admin")
        assert response.status_code == 200
        username = escape(authenticated_user.username)
        assert f"<h3>{username}</h3>" in response.text
        assert (
            f'hx-confirm="Are you sure you want to delete user \'{username}\'?"'
            in response.text
        )
        assert authenticated_user.username not in response.text

    def test_delete_user_popup(self, test_client, authenticated_user):
        response = test_client.get("/auth/user-admin", follow_redirects=True)
        assert response.status_code == 200
        assert b"hx-confirm=" in response.data
        assert b"Are you sure you want to delete user " in response.data

    def test_delete_current_user(self, test_client, authenticated_user):
        response = test_client.delete(
            f"/auth/user-admin/{authenticated_user.id}", follow_redirects=True
        )
        assert response.history[0].status_code == 303
        assert "/auth/user-admin" in response.history[0].headers["Location"]
        assert response.status_code == 200
        assert b"Forbidden to delete yourself!" in response.data
        assert User.query.filter_by(id=authenticated_user.id).first() is not None

    # This test relies on a test_user being created in an earlier test. Bad test design.
    def test_delete_user(self, test_client, authenticated_user):
        test_user = User.query.filter_by(username=TEST_USER["username"]).first()
        response = test_client.delete(
            f"/auth/user-admin/{test_user.id}", follow_redirects=True
        )
        assert response.history[0].status_code == 303
        assert "/auth/user-admin" in response.history[0].headers["Location"]
        assert response.status_code == 200
        assert b"Deleted user " in response.data
        assert User.query.filter_by(id=test_user.id).first() is None
