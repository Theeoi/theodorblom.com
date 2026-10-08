"""Views for the / url."""

from datetime import UTC, datetime, timedelta
from typing import cast

from flask import (
    Blueprint,
    render_template,
    request,
    send_from_directory,
)
from flask_login import current_user, login_required
from jinja2_fragments.flask import render_block

from stats import statistics

home = Blueprint("home", __name__, url_prefix="", static_folder="../static")


@home.route("/")
def index():
    """Definition of the / site."""

    return render_template("pages/home/index.html.jinja", user=current_user)


@home.put("/_user-nav")
def user_nav():
    return render_block(
        "components/_nav.html.jinja", "user_nav", user=current_user
    )


@home.put("/_admin-nav")
@login_required
def admin_nav():
    return render_block("components/_nav.html.jinja", "admin_nav")


@home.route("/robots.txt")
@home.route("/sitemap.xml")
def static_from_root():
    if home.static_folder is None:
        raise RuntimeError("Home blueprint has no static folder.")
    return send_from_directory(home.static_folder, request.path[1:])


@home.route("/stats")
@login_required
def stats():
    """Definition of the /stats page."""
    start = request.args.get("start", None)
    end = request.args.get("end", None)

    if start and end is not None:
        start_date = datetime.strptime(start, "%Y-%m-%d").replace(tzinfo=UTC)
        end_date = datetime.strptime(end, "%Y-%m-%d").replace(tzinfo=UTC)
    else:
        current_date = datetime.now(UTC)
        start_date = current_date - timedelta(days=7)
        end_date = current_date

    end_date = end_date.replace(hour=23, minute=59, second=59)

    stats: dict[str, object] = {}

    stats["routes"] = statistics.get_routes_data(start_date, end_date)
    stats["chart_data"] = statistics.get_chart_data(start_date, end_date)
    stats["hits"] = sum(cast(int, route.hits) for route in stats["routes"])
    stats["unique_users"] = statistics.get_unique_visitors(start_date, end_date)

    return render_template(
        "pages/home/stats.html.jinja",
        user=current_user,
        start_date=str(start_date.date()),
        end_date=str(end_date.date()),
        stats=stats,
    )
