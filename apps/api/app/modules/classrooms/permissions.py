from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.auth.service import AuthService


def get_current_teacher(
    token: str | None = Cookie(default=None, alias=settings.COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User:
    return AuthService(db).get_current_user(token)
