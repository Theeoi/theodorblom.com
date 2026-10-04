from collections.abc import Callable
from typing import TypeVar

from flask import Flask

_CallbackT = TypeVar("_CallbackT", bound=Callable[[str], object])

class UserMixin:
    @property
    def is_active(self) -> bool: ...
    @property
    def is_authenticated(self) -> bool: ...
    @property
    def is_anonymous(self) -> bool: ...
    def get_id(self) -> str | None: ...

class LoginManager:
    login_view: str | None

    def user_loader(self, callback: _CallbackT) -> _CallbackT: ...
    def init_app(
        self, app: Flask, add_context_processor: bool = True
    ) -> None: ...
