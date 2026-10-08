from app.database import db
from app.database.models import User


def load_user(user_id: str) -> User | None:
    return db.session.get(User, int(user_id))
