#!/usr/bin/env python
"""Views for the / url."""

import datetime
from flask_login import current_user, login_required
from flask import Blueprint, render_template, send_from_directory, request
from stats import statistics

home = Blueprint("home", __name__, url_prefix="", static_folder="../static")


@home.route("/")
def index():
    """Definition of the / site."""

    return render_template("index.html", user=current_user)


@home.route("/robots.txt")
@home.route("/sitemap.xml")
def static_from_root():
    return send_from_directory(home.static_folder, request.path[1:])


@home.route("/stats")
@login_required
def stats():
    """Definition of the /stats page."""
    start = request.args.get("start", None)
    end = request.args.get("end", None)

    if start and end is not None:
        start_date = datetime.datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end, "%Y-%m-%d")
    else:
        current_date = datetime.datetime.utcnow()
        start_date = current_date - datetime.timedelta(days=7)
        end_date = current_date

    end_date = end_date.replace(hour=23, minute=59, second=59)

    stats: dict = {}

    stats["routes"] = statistics.get_routes_data(start_date, end_date)
    stats["chart_data"] = statistics.get_chart_data(start_date, end_date)
    stats["hits"] = sum([route.hits for route in stats["routes"]])
    stats["unique_users"] = statistics.get_unique_visitors(start_date, end_date)

    return render_template(
        "stats.html",
        user=current_user,
        start_date=str(start_date.date()),
        end_date=str(end_date.date()),
        stats=stats,
    )
