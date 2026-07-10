from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}@example.com"


def _register_payload(email: str) -> dict[str, str]:
    return {
        "full_name": "Auth Cookie Teacher",
        "email": email,
        "password": "StrongPass123!",
    }


def test_login_sets_cookie_and_me_accepts_cookie() -> None:
    client = TestClient(app)
    email = _email("login-cookie")
    payload = _register_payload(email)

    register_response = client.post("/api/v1/auth/register", json=payload)
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": payload["password"]},
    )

    assert login_response.status_code == 200
    set_cookie = login_response.headers["set-cookie"]
    assert f"{settings.COOKIE_NAME}=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "Path=/" in set_cookie
    assert "Max-Age=3600" in set_cookie
    assert "Secure" not in set_cookie

    me_response = client.get(
        "/api/v1/auth/me",
        cookies={settings.COOKIE_NAME: login_response.cookies[settings.COOKIE_NAME]},
    )

    assert me_response.status_code == 200
    assert me_response.json()["data"]["email"] == email


def test_register_sets_cookie_for_immediate_session() -> None:
    client = TestClient(app)
    payload = _register_payload(_email("register-cookie"))

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201
    assert f"{settings.COOKIE_NAME}=" in response.headers["set-cookie"]
    assert response.cookies.get(settings.COOKIE_NAME)


def test_logout_clears_matching_cookie_and_me_requires_auth() -> None:
    client = TestClient(app)
    no_cookie_response = client.get("/api/v1/auth/me")
    assert no_cookie_response.status_code == 401
    assert no_cookie_response.json()["error"]["code"] == "NOT_AUTHENTICATED"

    response = client.post("/api/v1/auth/logout")

    assert response.status_code == 200
    set_cookie = response.headers["set-cookie"]
    assert f"{settings.COOKIE_NAME}=" in set_cookie
    assert "Max-Age=0" in set_cookie
    assert "Path=/" in set_cookie
    assert "SameSite=lax" in set_cookie


def test_cookie_security_flags_are_configurable(monkeypatch) -> None:
    client = TestClient(app)
    monkeypatch.setattr(settings, "COOKIE_SECURE", True)

    response = client.post("/api/v1/auth/register", json=_register_payload(_email("secure-cookie")))

    assert response.status_code == 201
    assert "Secure" in response.headers["set-cookie"]
