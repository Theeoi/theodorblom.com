from collections import defaultdict
from datetime import UTC, datetime
from typing import cast

from flask import Flask, Response, g, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, func, select
from sqlalchemy.engine import Row
from sqlalchemy.exc import SQLAlchemyError

from app.database.models import Request


class Statistics:
    def __init__(self) -> None:
        self.app: Flask | None = None
        self.db: SQLAlchemy | None = None
        self.model: type[Request] | None = None

    def init_app(
        self, app: Flask, db: SQLAlchemy, model: type[Request]
    ) -> None:
        self.app = app
        self.db = db
        self.model = model

        _ = self.app.before_request(self.before_request)
        _ = self.app.after_request(self.after_request)
        _ = self.app.teardown_request(self.teardown_request)

    def _require_initialized(
        self,
    ) -> tuple[Flask, SQLAlchemy, type[Request]]:
        if self.app is None or self.db is None or self.model is None:
            raise RuntimeError("Statistics has not been initialized.")
        return self.app, self.db, self.model

    def before_request(self) -> None:
        """Function called before handling any request."""
        g.request_date = datetime.now(UTC)

    def after_request(self, response: Response) -> Response:
        """Function called after handling any request."""

        return response

    def teardown_request(self, _exception: BaseException | None = None) -> None:
        """Function called on every request."""
        request_date = cast(datetime | None, g.get("request_date"))
        if request_date is None:
            return

        app, db, model = self._require_initialized()

        path = request.path
        obj: dict[str, object] = {
            "date": request_date,
            "path": path,
            "remote_address": request.environ.get(
                "HTTP_X_REAL_IP", request.remote_addr
            ),
            "referrer": request.referrer,
        }

        if "static" not in path:
            try:
                db.session.add(model(**obj))
                db.session.commit()
            except SQLAlchemyError as e:
                app.logger.warning(f"Error tearing down a request: {e}")

    def get_routes_data(
        self, start_date: datetime, end_date: datetime
    ) -> list[Row[tuple[str | None, int, int, datetime | None]]]:
        _, db, model = self._require_initialized()
        query = (
            db.session.query(
                model.path,
                func.count(model.path).label("hits"),
                func.count(model.remote_address.distinct()).label(
                    "unique_hits"
                ),
                func.max(model.date).label("last_requested"),
            )
            .group_by(model.path)
            .order_by(desc("hits"))
            .filter(model.date.between(start_date, end_date))
        )

        return query.all()

    def get_chart_data(
        self, start_date: datetime, end_date: datetime
    ) -> tuple[list[dict[str, str | int]], list[dict[str, str | int]]]:
        _, db, model = self._require_initialized()
        requests = db.session.execute(
            select(model.date, model.remote_address).where(
                model.date.between(start_date, end_date)
            )
        ).tuples()

        hits_dict: dict[str, int] = defaultdict(int)
        unique_hits_dict: dict[str, set[str]] = defaultdict(set)

        for request_date, remote_address in requests:
            if request_date is None:
                continue
            date_key = request_date.date().isoformat()
            hits_dict[date_key] += 1
            if remote_address is not None:
                unique_hits_dict[date_key].add(remote_address)

        hits = [{"x": date, "y": count} for date, count in hits_dict.items()]
        unique_hits = [
            {"x": date, "y": len(ip_set)}
            for date, ip_set in unique_hits_dict.items()
        ]

        return hits, unique_hits

    def get_unique_visitors(
        self, start_date: datetime, end_date: datetime
    ) -> int:
        _, db, model = self._require_initialized()
        query = (
            db.session.query(model)
            .group_by(model.remote_address)
            .filter(model.date.between(start_date, end_date))
        )

        return query.count()
