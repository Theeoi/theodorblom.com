#!/usr/bin/env python
import datetime
from collections import defaultdict
from flask import g, request, Response
from flask_sqlalchemy.query import Query
from sqlalchemy import func, desc
from typing import Tuple, List, Dict


class Statistics:
    def init_app(self, app, db, model) -> None:
        self.app = app
        self.db = db
        self.model = model

        self.app.before_request(self.before_request)
        self.app.after_request(self.after_request)
        self.app.teardown_request(self.teardown_request)

    def before_request(self) -> None:
        """Function called before handling any request."""
        g.request_date = datetime.datetime.utcnow()

    def after_request(self, response: Response) -> Response:
        """Function called after handling any request."""

        return response

    def teardown_request(self, exception=None):
        """Function called on every request."""
        try:
            obj: dict = {}

            obj["date"] = g.request_date
            obj["path"] = request.path
            obj["remote_address"] = request.environ.get(
                "HTTP_X_REAL_IP", request.remote_addr
            )
            obj["referrer"] = request.referrer

            if "static" not in obj["path"]:
                self.db.session.add(self.model(**obj))
                self.db.session.commit()

        except Exception as e:
            self.app.logger.warning(f"Error tearing down a request: {e}")

    def _add_date_filter_to_query(
        self, query: Query, start_date: datetime.datetime, end_date: datetime.datetime
    ) -> Query:
        return query.filter(self.model.date.between(start_date, end_date))

    def get_routes_data(
        self, start_date: datetime.datetime, end_date: datetime.datetime
    ) -> list:
        query = (
            self.db.session.query(
                self.model.path,
                func.count(self.model.path).label("hits"),
                func.count(self.model.remote_address.distinct()).label("unique_hits"),
                func.max(self.model.date).label("last_requested"),
            )
            .group_by(self.model.path)
            .order_by(desc("hits"))
        )

        query = self._add_date_filter_to_query(query, start_date, end_date)

        return query.all()

    def get_chart_data(
        self, start_date: datetime.datetime, end_date: datetime.datetime
    ) -> Tuple[List[Dict], List[Dict]]:
        query = self.db.session.query(self.model.date, self.model.remote_address)
        query = self._add_date_filter_to_query(query, start_date, end_date)

        requests = query.all()

        hits_dict = defaultdict(int)
        unique_hits_dict = defaultdict(set)

        for req in requests:
            hits_dict[str(req.date.date())] += 1
            unique_hits_dict[str(req.date.date())].add(req.remote_address)

        hits = [{"x": date, "y": count} for date, count in hits_dict.items()]
        unique_hits = [
            {"x": date, "y": len(ip_set)} for date, ip_set in unique_hits_dict.items()
        ]

        return hits, unique_hits

    def get_unique_visitors(
        self, start_date: datetime.datetime, end_date: datetime.datetime
    ) -> int:
        query = self.db.session.query(self.model).group_by(self.model.remote_address)

        query = self._add_date_filter_to_query(query, start_date, end_date)

        return query.count()
