from datetime import timedelta
from uuid import UUID

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import ALGORITHM, create_access_token, hash_password, verify_password
from app.modules.auth.errors import (
    email_already_registered,
    inactive_user,
    invalid_credentials,
    not_authenticated,
)
from app.modules.auth.models import User
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import UserLogin, UserRegister


class AuthService:
    def __init__(self, db: Session) -> None:
        self.repository = AuthRepository(db)

    def register(self, payload: UserRegister) -> User:
        email = payload.email.lower()
        existing_user = self.repository.get_by_email(email)
        if existing_user is not None:
            raise email_already_registered()

        return self.repository.create_teacher(
            full_name=payload.full_name.strip(),
            email=email,
            password_hash=hash_password(payload.password),
        )

    def login(self, payload: UserLogin) -> tuple[User, str]:
        user = self.repository.get_by_email(payload.email.lower())
        if user is None or user.deleted_at is not None:
            raise invalid_credentials()
        if not user.is_active:
            raise inactive_user()
        if not verify_password(payload.password, user.password_hash):
            raise invalid_credentials()

        token = create_access_token(
            subject=str(user.id),
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        return user, token

    def get_current_user(self, token: str | None) -> User:
        if not token:
            raise not_authenticated()

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            subject = payload.get("sub")
            if subject is None:
                raise not_authenticated()
            user_id = UUID(subject)
        except (JWTError, ValueError):
            raise not_authenticated() from None

        user = self.repository.get_by_id(user_id)
        if user is None:
            raise not_authenticated()
        if not user.is_active:
            raise inactive_user()
        return user
