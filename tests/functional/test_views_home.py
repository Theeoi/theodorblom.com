import pytest
from flask.testing import FlaskClient


def test_robots(test_client: FlaskClient):
    with test_client.get("/robots.txt") as response:
        assert response.status_code == 200


def test_sitemap(test_client: FlaskClient):
    response = test_client.get("/sitemap.xml")
    assert response.status_code == 200


class TestBase:
    def test_header(self, test_client: FlaskClient):
        response = test_client.get("/")
        assert response.status_code == 200
        assert b'<h1 id="typeit"' in response.get_data()
        assert b'<button class="nav-toggle"' in response.get_data()
        assert b'<nav class="nav"' in response.get_data()

    def test_footer(self, test_client: FlaskClient):
        response = test_client.get("/")
        assert response.status_code == 200
        assert b'<div id="made-with"' in response.get_data()
        assert b'<div id="copyright"' in response.get_data()
        assert b'<div id="login"' in response.get_data()

    def test_footer_login(self, test_client: FlaskClient):
        response = test_client.get("/")
        assert response.status_code == 200
        assert b"href='/auth/login'>Login" in response.get_data()

    @pytest.mark.usefixtures("authenticated_user")
    def test_footer_logout(self, test_client: FlaskClient):
        response = test_client.get("/")
        assert response.status_code == 200
        assert b"href='/auth/logout'>Logout" in response.get_data()


class TestIndex:
    def test_index(self, test_client: FlaskClient):
        response = test_client.get("/")
        assert response.status_code == 200
        assert b"/img/landing.jpg" in response.get_data()
        assert b'<h1 id="typeit">Theodor Blom</h1>' in response.get_data()

    def test_index_post(self, test_client: FlaskClient):
        response = test_client.post("/")
        assert response.status_code == 405


class TestStats:
    def test_stats_redirect(self, test_client: FlaskClient):
        response = test_client.get("/stats")
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]

    @pytest.mark.usefixtures("authenticated_user")
    def test_stats(self, test_client: FlaskClient):
        response = test_client.get("/stats")
        assert response.status_code == 200
        assert b"Stats" in response.get_data()
        assert b'<form id="dateinput"' in response.get_data()
        assert b'<div id="hits"' in response.get_data()
        assert b'<div id="unique"' in response.get_data()
        assert b'<div id="chart"' in response.get_data()
        assert b"<table>" in response.get_data()

    @pytest.mark.usefixtures("authenticated_user")
    def test_stats_with_data(self, test_client: FlaskClient):
        DATA = {"start": "2023-01-01", "end": "2023-01-14"}
        response = test_client.get("/stats", query_string=DATA)
        assert response.status_code == 200
        assert b"Stats" in response.get_data()
        assert b'name="start" value="2023-01-01"' in response.get_data()
        assert b'name="end" value="2023-01-14"' in response.get_data()
