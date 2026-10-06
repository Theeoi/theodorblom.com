from datetime import date, datetime

import pytest
from flask.testing import FlaskClient
from sqlalchemy import select
from werkzeug.security import check_password_hash

from app.database import db
from app.database.models import Blogpost, Request, User


@pytest.mark.usefixtures("test_client")
class TestUser:
    def test_instance(self, admin_user: User) -> None:
        assert isinstance(admin_user.id, int)
        assert admin_user.username == "adminPhil"
        assert admin_user.password is not None
        assert admin_user.password != "superphilsPassword123"
        assert (
            check_password_hash(admin_user.password, "superphilsPassword123")
            is True
        )
        assert isinstance(admin_user.date_created, datetime)

    def test_database_entry(self, admin_user: User) -> None:
        user = db.session.scalar(select(User).where(User.id == admin_user.id))
        assert user is not None
        assert isinstance(user.id, int)
        assert user.username == admin_user.username
        assert user.password == admin_user.password
        assert isinstance(user.date_created, datetime)


@pytest.mark.usefixtures("test_client")
class TestBlogpost:
    def test_instance(self, blogpost: Blogpost) -> None:
        assert isinstance(blogpost.id, int)
        assert blogpost.slug == "blogpost-in-testing"
        assert blogpost.title == "Blogpost in Testing"
        assert blogpost.tags == "test, pytest, blogpost"
        assert blogpost.content == "This is a test blogpost!"
        assert isinstance(blogpost.published, bool)
        assert isinstance(blogpost.date_created, date)

    def test_database_entry(self, blogpost: Blogpost) -> None:
        post = db.session.scalar(
            select(Blogpost).where(Blogpost.id == blogpost.id)
        )
        assert post is not None
        assert isinstance(post.id, int)
        assert post.slug == post.slug
        assert post.title == post.title
        assert post.tags == post.tags
        assert post.content == post.content
        assert isinstance(post.published, bool)
        assert isinstance(post.date_created, date)


@pytest.mark.usefixtures("test_client")
class TestRequest:
    @pytest.mark.skip(reason="Not implemented")
    def test_instance(self) -> None:
        pass

    def test_database_entry(self, test_client: FlaskClient) -> None:
        response = test_client.get("/")
        assert response.status_code == 200

        request = db.session.scalar(
            select(Request).order_by(Request.date.desc())
        )
        assert request is not None
        assert isinstance(request.index, int)
        assert isinstance(request.date, datetime)
        assert request.path == "/"
        assert request.remote_address == "127.0.0.1"
        assert request.referrer is None
