"""Define database models."""

from datetime import datetime
from typing import ClassVar

from flask_login import UserMixin
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import db


class User(db.Model, UserMixin):
    """Database model for a website user."""

    __bind_key__: ClassVar[str] = "auth"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str | None] = mapped_column(String(50), unique=True)
    password: Mapped[str | None] = mapped_column(String(100))
    date_created: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )


class Blogpost(db.Model):
    """Database model for a blogpost."""

    __bind_key__: ClassVar[str] = "blog"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str | None] = mapped_column(String(120), unique=True)
    title: Mapped[str] = mapped_column(String(100))
    tags: Mapped[str | None] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text)
    published: Mapped[bool | None] = mapped_column(index=True)
    date_created: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=func.now(), index=True
    )


class Request(db.Model):
    """Database model for a webpage request. Used for website statistics."""

    index: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    path: Mapped[str | None] = mapped_column(String())
    remote_address: Mapped[str | None] = mapped_column()
    referrer: Mapped[str | None] = mapped_column()
