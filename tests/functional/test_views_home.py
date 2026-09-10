#!/usr/bin/env python

import datetime
import json
from urllib.parse import quote

from markupsafe import escape

from app.database import db
from app.database.models import Request


def test_robots(test_client):
    response = test_client.get("/robots.txt")
    assert response.status_code == 200


def test_sitemap(test_client):
    response = test_client.get("/sitemap.xml")
    assert response.status_code == 200


class TestBase:
    def test_header(self, test_client):
        response = test_client.get("/")
        assert response.status_code == 200
        assert b'<h1 id="typeit"' in response.data
        assert b'<button class="nav-toggle"' in response.data
        assert b'<nav class="nav"' in response.data

    def test_footer(self, test_client):
        response = test_client.get("/")
        assert response.status_code == 200
        assert b'<div id="made-with"' in response.data
        assert b'<div id="copyright"' in response.data
        assert b'<div id="login"' in response.data

    def test_footer_login(self, test_client):
        response = test_client.get("/")
        assert response.status_code == 200
        assert b"href='/auth/login'>Login" in response.data

    def test_footer_logout(self, test_client, authenticated_user):
        response = test_client.get("/")
        assert response.status_code == 200
        assert b"href='/auth/logout'>Logout" in response.data


class TestIndex:
    def test_index(self, test_client):
        response = test_client.get("/")
        assert response.status_code == 200
        assert b"/img/landing.jpg" in response.data
        assert b'<h1 id="typeit">Theodor Blom</h1>' in response.data

    def test_index_post(self, test_client):
        response = test_client.post("/")
        assert response.status_code == 405


class TestStats:
    def test_logged_path_is_escaped(self, test_client, request):
        """A visitor's logged URL must display as text when an admin reads stats."""
        path = '/escaping-regression/<b title="quotes & \'apostrophes\'">marker</b>'
        try:
            response = test_client.get(quote(path, safe="/"))
            assert response.status_code == 404
            logged_request = Request.query.filter_by(path=path).first()
            assert logged_request is not None

            date = logged_request.date.date()
            # Authenticate only after the anonymous request has been recorded.
            request.getfixturevalue("authenticated_user")
            response = test_client.get(
                "/stats",
                query_string={
                    "start": (date - datetime.timedelta(days=1)).isoformat(),
                    "end": (date + datetime.timedelta(days=1)).isoformat(),
                },
            )
            assert response.status_code == 200
            assert f"<td>{escape(path)}</td>" in response.text
            assert path not in response.text
        finally:
            Request.query.filter_by(path=path).delete()
            db.session.commit()

    def test_chart_data_remains_json(self, test_client, authenticated_user):
        """HTML escaping must not turn the chart's JSON into HTML entities."""
        date = datetime.datetime.utcnow().date()
        response = test_client.get(
            "/stats",
            query_string={
                "start": (date - datetime.timedelta(days=1)).isoformat(),
                "end": (date + datetime.timedelta(days=1)).isoformat(),
            },
        )
        assert response.status_code == 200
        chart_json = response.text.split("window.userChartData = ", 1)[1].split(
            "</script>", 1
        )[0]
        hits, unique_hits = json.loads(chart_json)
        for series in (hits, unique_hits):
            assert any(
                point["x"] == date.isoformat() and point["y"] >= 1
                for point in series
            )

    def test_stats_redirect(self, test_client):
        response = test_client.get("/stats")
        assert response.status_code == 302
        assert "/auth/login" in response.headers["Location"]

    def test_stats(self, test_client, authenticated_user):
        response = test_client.get("/stats")
        assert response.status_code == 200
        assert b"Stats" in response.data
        assert b'<form id="dateinput"' in response.data
        assert b'<div id="hits"' in response.data
        assert b'<div id="unique"' in response.data
        assert b'<div id="chart"' in response.data
        assert b"<table>" in response.data

    def test_stats_with_data(self, test_client, authenticated_user):
        DATA = {"start": "2023-01-01", "end": "2023-01-14"}
        response = test_client.get("/stats", query_string=DATA)
        assert response.status_code == 200
        assert b"Stats" in response.data
        assert b'name="start" value="2023-01-01"' in response.data
        assert b'name="end" value="2023-01-14"' in response.data
