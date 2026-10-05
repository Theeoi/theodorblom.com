from collections.abc import Callable
from typing import Protocol, TypeVar

from flask import Flask
from werkzeug.local import LocalProxy

_CallbackT = TypeVar("_CallbackT", bound=Callable[[str], object])

class _CurrentUser(Protocol):
    id: int
    username: str
    is_authenticated: bool

current_user: LocalProxy[_CurrentUser]

def login_required[**P, R](func: Callable[P, R]) -> Callable[P, R]: ...
def login_user(user: UserMixin, remember: bool = False) -> bool: ...
def logout_user() -> None: ...

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
