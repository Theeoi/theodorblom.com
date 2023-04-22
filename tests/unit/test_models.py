#!/usr/bin/env python

import pytest
from datetime import datetime, date
from werkzeug.security import check_password_hash
from website.models import User, Blogpost, Request


class TestUser():
    def test_instance(self, test_client, admin_user):
        assert isinstance(admin_user.id, int)
        assert admin_user.username == 'adminPhil'
        assert admin_user.password != 'superphilsPassword123'
        assert check_password_hash(
            admin_user.password, 'superphilsPassword123') is True
        assert isinstance(admin_user.date_created, datetime)

    def test_database_entry(self, test_client, admin_user):
        query = User.query.filter_by(id=admin_user.id).first()
        assert isinstance(query.id, int)
        assert query.username == admin_user.username
        assert query.password == admin_user.password
        assert isinstance(query.date_created, datetime)


class TestBlogpost():
    def test_instance(self, test_client, blogpost):
        assert isinstance(blogpost.id, int)
        assert blogpost.slug == 'blogpost-in-testing'
        assert blogpost.title == 'Blogpost in Testing'
        assert blogpost.tags == 'test, pytest, blogpost'
        assert blogpost.content == 'This is a test blogpost!'
        assert isinstance(blogpost.published, bool)
        assert isinstance(blogpost.date_created, date)

    def test_database_entry(self, test_client, blogpost):
        query = Blogpost.query.filter_by(id=blogpost.id).first()
        assert isinstance(query.id, int)
        assert query.slug == blogpost.slug
        assert query.title == blogpost.title
        assert query.tags == blogpost.tags
        assert query.content == blogpost.content
        assert isinstance(query.published, bool)
        assert isinstance(query.date_created, date)


class TestRequest():
    @pytest.mark.skip(reason="Not implemented")
    def test_instance(self, test_client):
        pass

    def test_database_entry(self, test_client):
        response = test_client.get('/')
        assert response.status_code == 200

        request = Request.query.order_by(Request.date.desc()).first()
        assert isinstance(request.index, int)
        assert isinstance(request.date, datetime)
        assert request.path == '/'
        assert request.remote_address == '127.0.0.1'
        assert request.referrer is None
