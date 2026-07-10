from fastapi import APIRouter, Cookie, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import success_response
from app.db.session import get_db
from app.modules.auth.schemas import UserLogin, UserRead, UserRegister
from app.modules.auth.service import AuthService


router = APIRouter()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        path=settings.COOKIE_PATH,
        domain=settings.cookie_domain,
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        path=settings.COOKIE_PATH,
        domain=settings.cookie_domain,
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    payload: UserRegister,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> dict:
    user, token = service.register(payload)
    set_auth_cookie(response, token)
    return success_response(data=UserRead.model_validate(user).model_dump(mode="json"))


@router.post("/login")
def login(
    payload: UserLogin,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> dict:
    user, token = service.login(payload)
    set_auth_cookie(response, token)
    return success_response(data=UserRead.model_validate(user).model_dump(mode="json"))


@router.post("/logout")
def logout(response: Response) -> dict:
    clear_auth_cookie(response)
    return success_response(data={})


@router.get("/me")
def me(
    token: str | None = Cookie(default=None, alias=settings.COOKIE_NAME),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    user = service.get_current_user(token)
    return success_response(data=UserRead.model_validate(user).model_dump(mode="json"))
