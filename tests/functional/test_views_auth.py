import pytest
from _pytest.monkeypatch import MonkeyPatch
from flask.testing import FlaskClient
from flask_login import current_user
from sqlalchemy import select
from werkzeug.security import check_password_hash

from app.database import db
from app.database.models import User

TEST_USER: dict[str, str] = {
    "username": "testingPhil",
    "password1": "philsPassword123",
    "password2": "philsPassword123",
}


def _is_authenticated() -> bool:
    return bool(getattr(current_user, "is_authenticated", False))


class TestLogin:
    def test_login_page(self, test_client: FlaskClient) -> None:
        response = test_client.get("auth/login")
        assert not _is_authenticated()
        assert response.status_code == 200
        assert b"Login" in response.get_data()

    @pytest.mark.usefixtures("admin_user")
    def test_login_success(
        self, test_client: FlaskClient, admin_credentials: dict[str, str]
    ) -> None:
        response = test_client.post(
            "/auth/login", data=admin_credentials, follow_redirects=True
        )
        assert response.status_code == 200
        assert _is_authenticated() is True
        assert b"Logged in!" in response.get_data()
        assert b"Logout" in response.get_data()

    @pytest.mark.usefixtures("authenticated_user")
    def test_logout(self, test_client: FlaskClient) -> None:
        assert _is_authenticated() is True
        response = test_client.get("/auth/logout", follow_redirects=True)
        assert response.status_code == 200
        assert not _is_authenticated()
        assert b"Login" in response.get_data()

    @pytest.mark.usefixtures("admin_user")
    def test_login_wrong_password(
        self, test_client: FlaskClient, admin_credentials: dict[str, str]
    ) -> None:
        data: dict[str, str] = {
            "username": admin_credentials["username"],
            "password": "Password123",
        }
        response = test_client.post(
            "/auth/login", data=data, follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Password is incorrect" in response.get_data()
        assert not _is_authenticated()

    def test_login_invalid_user(
        self, test_client: FlaskClient, admin_credentials: dict[str, str]
    ) -> None:
        response = test_client.post(
            "/auth/login", data=admin_credentials, follow_redirects=True
        )
        assert response.status_code == 200
        assert b"User does not exist" in response.get_data()
        assert not _is_authenticated()


class TestCreateUser:
    def test_user_admin_redirect(self, test_client: FlaskClient) -> None:
        response = test_client.get("/auth/user-admin")
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]

    @pytest.mark.usefixtures("authenticated_user")
    def test_create_user_success(self, test_client: FlaskClient) -> None:
        response = test_client.post(
            "/auth/user-admin", data=TEST_USER, follow_redirects=True
        )
        assert response.status_code == 200
        assert (
            db.session.scalar(
                select(User).where(User.username == TEST_USER["username"])
            )
            is not None
        )

    @pytest.mark.usefixtures("authenticated_user")
    def test_create_duplicate_user(self, test_client: FlaskClient) -> None:
        response = test_client.post(
            "/auth/user-admin", data=TEST_USER, follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Username already exists." in response.get_data()
        assert (
            db.session.scalar(
                select(User).where(User.username == TEST_USER["username"])
            )
            is not None
        )

    @pytest.mark.usefixtures("authenticated_user")
    def test_create_user_password_mismatch(
        self, test_client: FlaskClient
    ) -> None:
        data: dict[str, str] = {
            "username": "mismatchPhil",
            "password1": "philsPassword123",
            "password2": "philsPassword1234",
        }
        response = test_client.post(
            "/auth/user-admin", data=data, follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Passwords do not match." in response.get_data()
        assert (
            db.session.scalar(
                select(User).where(User.username == "mismatchPhil")
            )
            is None
        )

    @pytest.mark.usefixtures("authenticated_user")
    def test_create_user_short_username(self, test_client: FlaskClient) -> None:
        data: dict[str, str] = {
            "username": "P",
            "password1": "philsPassword123",
            "password2": "philsPassword123",
        }
        response = test_client.post(
            "/auth/user-admin", data=data, follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Username is too short." in response.get_data()
        assert (
            db.session.scalar(select(User).where(User.username == "P")) is None
        )

    @pytest.mark.usefixtures("authenticated_user")
    def test_create_user_short_password(self, test_client: FlaskClient) -> None:
        data: dict[str, str] = {
            "username": "shortPhil",
            "password1": "12345",
            "password2": "12345",
        }
        response = test_client.post(
            "/auth/user-admin", data=data, follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Password is too short." in response.get_data()
        assert (
            db.session.scalar(select(User).where(User.username == "shortPhil"))
            is None
        )


class TestChangeUserPwd:
    def test_change_pwd_form(
        self, test_client: FlaskClient, authenticated_user: User
    ) -> None:
        response = test_client.patch(
            f"/auth/user-admin/{authenticated_user.id}", follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Repeat new password" in response.get_data()

    def test_change_pwd_form_closes(
        self, test_client: FlaskClient, authenticated_user: User
    ) -> None:
        response = test_client.patch(
            f"/auth/user-admin/{authenticated_user.id}?close=1"
        )
        assert response.status_code == 200
        content = response.get_data(as_text=True)
        assert content.count('class="user-card"') == 1
        assert "fa-key" in content
        assert "fa-x" not in content
        assert 'aria-label="Change password"' in content
        assert 'class="change-pwd"' not in content

    def test_change_pwd_form_returns_complete_card(
        self, test_client: FlaskClient, authenticated_user: User
    ) -> None:
        response = test_client.patch(
            f"/auth/user-admin/{authenticated_user.id}"
        )
        assert response.status_code == 200
        content = response.get_data(as_text=True)
        assert content.count('class="user-card"') == 1
        assert 'class="change-pwd"' in content
        assert "fa-x" in content
        assert "fa-key" not in content
        assert 'aria-label="Close password form"' in content
        assert f'action="/auth/user-admin/{authenticated_user.id}"' in content
        assert 'hx-target="closest .user-card"' in content
        assert 'hx-swap="outerHTML"' in content
        assert 'hx-disabled-elt="this"' in content
        assert f'id="old_password-{authenticated_user.id}"' in content
        assert 'hx-get=""' not in content

    def test_change_user_pwd_old_mismatch(
        self, test_client: FlaskClient, authenticated_user: User
    ) -> None:
        original_hash = authenticated_user.password
        data: dict[str, str] = {
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
        assert b"Current password is incorrect." in response.get_data()
        db.session.refresh(authenticated_user)
        assert authenticated_user.password == original_hash

    def test_change_user_pwd_short_password(
        self,
        test_client: FlaskClient,
        authenticated_user: User,
        admin_credentials: dict[str, str],
    ) -> None:
        original_hash = authenticated_user.password
        data: dict[str, str] = {
            "old_password": admin_credentials["password"],
            "new_password1": "12345",
            "new_password2": "12345",
        }
        response = test_client.post(
            f"/auth/user-admin/{authenticated_user.id}",
            data=data,
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Password is too short." in response.get_data()
        db.session.refresh(authenticated_user)
        assert authenticated_user.password == original_hash

    def test_change_user_pwd_new_mismatch(
        self,
        test_client: FlaskClient,
        authenticated_user: User,
        admin_credentials: dict[str, str],
    ) -> None:
        original_hash = authenticated_user.password
        data: dict[str, str] = {
            "old_password": admin_credentials["password"],
            "new_password1": "philsPassword321",
            "new_password2": "philsPassword3210",
        }
        response = test_client.post(
            f"/auth/user-admin/{authenticated_user.id}",
            data=data,
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Passwords do not match." in response.get_data()
        db.session.refresh(authenticated_user)
        assert authenticated_user.password == original_hash

    def test_change_user_pwd_success(
        self,
        test_client: FlaskClient,
        authenticated_user: User,
        admin_credentials: dict[str, str],
        monkeypatch: MonkeyPatch,
    ) -> None:
        user_id = authenticated_user.id
        original_hash = authenticated_user.password
        # Statistics teardown commits the shared session and could hide a missing commit.
        monkeypatch.setitem(
            test_client.application.teardown_request_funcs, None, []
        )
        data: dict[str, str] = {
            "old_password": admin_credentials["password"],
            "new_password1": "philsPassword321",
            "new_password2": "philsPassword321",
        }
        response = test_client.post(
            f"/auth/user-admin/{user_id}",
            data=data,
            follow_redirects=True,
        )
        assert response.history[0].status_code == 302
        assert response.history[0].headers["Location"] == "/auth/user-admin"
        assert response.status_code == 200
        assert b"Successfully changed password!" in response.get_data()

        db.session.remove()
        stored_hash: str | None = db.session.scalar(
            select(User.password).where(User.id == user_id)
        )
        assert stored_hash is not None
        assert stored_hash != original_hash
        assert stored_hash != data["new_password1"]
        assert stored_hash.startswith("scrypt:")
        assert check_password_hash(stored_hash, data["new_password1"])
        assert not check_password_hash(
            stored_hash, admin_credentials["password"]
        )

        _ = test_client.get("/auth/logout", follow_redirects=True)
        assert not _is_authenticated()
        response = test_client.post(
            "/auth/login", data=admin_credentials, follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Password is incorrect." in response.get_data()
        assert not _is_authenticated()

        response = test_client.post(
            "/auth/login",
            data={
                "username": admin_credentials["username"],
                "password": data["new_password1"],
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Logged in!" in response.get_data()
        assert _is_authenticated() is True

    def test_change_user_pwd_unauthorized(
        self,
        test_client: FlaskClient,
        admin_user: User,
        admin_credentials: dict[str, str],
    ) -> None:
        original_hash = admin_user.password
        data: dict[str, str] = {
            "old_password": admin_credentials["password"],
            "new_password1": "philsPassword321",
            "new_password2": "philsPassword321",
        }
        response = test_client.post(
            f"/auth/user-admin/{admin_user.id}", data=data
        )
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]
        db.session.refresh(admin_user)
        assert admin_user.password is not None
        assert admin_user.password == original_hash
        assert check_password_hash(
            admin_user.password, admin_credentials["password"]
        )


class TestDeleteUser:
    @pytest.mark.usefixtures("authenticated_user")
    def test_delete_user_popup(self, test_client: FlaskClient) -> None:
        response = test_client.get("/auth/user-admin", follow_redirects=True)
        assert response.status_code == 200
        assert b"hx-confirm=" in response.get_data()
        assert b"Are you sure you want to delete user " in response.get_data()

    def test_delete_current_user(
        self, test_client: FlaskClient, authenticated_user: User
    ) -> None:
        response = test_client.delete(
            f"/auth/user-admin/{authenticated_user.id}", follow_redirects=True
        )
        assert response.history[0].status_code == 303
        assert "/auth/user-admin" in response.history[0].headers["Location"]
        assert response.status_code == 200
        assert b"Forbidden to delete yourself!" in response.get_data()
        assert (
            db.session.scalar(
                select(User).where(User.id == authenticated_user.id)
            )
            is not None
        )

    # This test relies on a test_user being created in an earlier test.
    # Bad test design.
    @pytest.mark.usefixtures("authenticated_user")
    def test_delete_user(self, test_client: FlaskClient) -> None:
        test_user: User | None = db.session.scalar(
            select(User).where(User.username == TEST_USER["username"])
        )
        assert test_user is not None
        response = test_client.delete(
            f"/auth/user-admin/{test_user.id}", follow_redirects=True
        )
        assert response.history[0].status_code == 303
        assert "/auth/user-admin" in response.history[0].headers["Location"]
        assert response.status_code == 200
        assert b"Deleted user " in response.get_data()
        assert (
            db.session.scalar(select(User).where(User.id == test_user.id))
            is None
        )
