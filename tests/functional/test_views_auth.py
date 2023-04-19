#!/usr/bin/env python

from conftest import ADMIN_USER
from website.models import User
from flask_login import current_user

TEST_USER = {
    'username': 'testingPhil',
    'password1': 'philsPassword123',
    'password2': 'philsPassword123'
}


class TestLogin():
    def test_login_page(self, test_client):
        response = test_client.get('auth/login')
        assert current_user.is_authenticated is False
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_login_success(self, test_client, admin_user):
        response = test_client.post('/auth/login',
                                    data=ADMIN_USER,
                                    follow_redirects=True)
        assert response.status_code == 200
        assert current_user.is_authenticated is True
        assert b'Logged in!' in response.data
        assert b'Logout' in response.data

    def test_logout(self, test_client, authenticated_user):
        assert current_user.is_authenticated is True
        response = test_client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        assert current_user.is_authenticated is False
        assert b'Login' in response.data

    def test_login_wrong_password(self, test_client, admin_user):
        data = {
            'username': ADMIN_USER['username'],
            'password': 'Password123',
        }
        response = test_client.post('/auth/login',
                                    data=data,
                                    follow_redirects=True)
        assert response.status_code == 200
        assert b'Password is incorrect' in response.data
        assert current_user.is_authenticated is False

    def test_login_invalid_user(self, test_client):
        response = test_client.post('/auth/login',
                                    data=ADMIN_USER,
                                    follow_redirects=True)
        assert response.status_code == 200
        assert b'User does not exist' in response.data
        assert current_user.is_authenticated is False


class TestCreateUser():
    def test_create_user_redirect(self, test_client):
        response = test_client.get('/auth/create-user')
        assert response.status_code == 302
        assert '/auth/login' in response.headers['Location']

    def test_create_user_success(self, test_client, authenticated_user):
        response = test_client.post('/auth/create-user', data=TEST_USER,
                                    follow_redirects=True)
        assert response.status_code == 200
        assert User.query.filter_by(
            username=TEST_USER['username']).first() is not None

    def test_create_duplicate_user(self, test_client, authenticated_user):
        response = test_client.post('/auth/create-user', data=TEST_USER,
                                    follow_redirects=True)
        assert response.status_code == 200
        assert b'Username already exists.' in response.data
        assert User.query.filter_by(
            username=TEST_USER['username']).first() is not None

    def test_create_user_password_mismatch(self, test_client,
                                           authenticated_user):
        DATA = {
            'username': 'mismatchPhil',
            'password1': 'philsPassword123',
            'password2': 'philsPassword1234'
        }
        response = test_client.post('/auth/create-user', data=DATA,
                                    follow_redirects=True)
        assert response.status_code == 200
        assert b'Passwords do not match.' in response.data
        assert User.query.filter_by(username='mismatchPhil').first() is None

    def test_create_user_short_username(self, test_client, authenticated_user):
        DATA = {
            'username': 'P',
            'password1': 'philsPassword123',
            'password2': 'philsPassword123'
        }
        response = test_client.post('/auth/create-user', data=DATA,
                                    follow_redirects=True)
        assert response.status_code == 200
        assert b'Username is too short.' in response.data
        assert User.query.filter_by(username='P').first() is None

    def test_create_user_short_password(self, test_client, authenticated_user):
        DATA = {
            'username': 'shortPhil',
            'password1': '12345',
            'password2': '12345'
        }
        response = test_client.post('/auth/create-user', data=DATA,
                                    follow_redirects=True)
        assert response.status_code == 200
        assert b'Password is too short.' in response.data
        assert User.query.filter_by(username='shortPhil').first() is None
