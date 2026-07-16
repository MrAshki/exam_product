from __future__ import annotations

from decimal import Decimal
from typing import Any

import httpx
import pytest

from app.core.config import settings
from app.core.exceptions import AppException
from app.modules.ai.gateway import ModelGateway
from app.modules.ai.providers import GeminiProvider, MockProvider, OpenRouterProvider, build_provider
from app.modules.ai.schemas import AICallContext, GatewayResult
from app.modules.ai.service import AIService
from app.modules.ai.task_config import (
    TASK_ESSAY_GRADING,
    TASK_SHORT_ANSWER_GRADING,
    TASK_SUGGEST_ESSAY_RUBRIC,
    get_task_model_config,
)


PRIMARY = "unit/primary:free"
FALLBACK = "unit/fallback:free"


@pytest.fixture
def openrouter_settings(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "openrouter")
    monkeypatch.setattr(settings, "AI_MODEL", "gemini-2.0-flash")
    monkeypatch.setattr(settings, "AI_TIMEOUT_SECONDS", 17)
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setattr(settings, "OPENROUTER_BASE_URL", "https://openrouter.test/api/v1")
    monkeypatch.setattr(settings, "OPENROUTER_SITE_URL", "")
    monkeypatch.setattr(settings, "OPENROUTER_APP_NAME", "Unit Test App")
    monkeypatch.setattr(settings, "OPENROUTER_REQUIRE_FREE_MODELS", True)
    monkeypatch.setattr(settings, "AI_SUGGEST_ESSAY_RUBRIC_PRIMARY_MODEL", "unit/rubric-primary:free")
    monkeypatch.setattr(settings, "AI_SUGGEST_ESSAY_RUBRIC_FALLBACK_MODEL", "unit/rubric-fallback:free")
    monkeypatch.setattr(settings, "AI_SUGGEST_ESSAY_RUBRIC_TEMPERATURE", 0.2)
    monkeypatch.setattr(settings, "AI_SUGGEST_ESSAY_RUBRIC_MAX_TOKENS", 1200)
    monkeypatch.setattr(settings, "AI_SHORT_ANSWER_GRADING_PRIMARY_MODEL", "unit/short-primary:free")
    monkeypatch.setattr(settings, "AI_SHORT_ANSWER_GRADING_FALLBACK_MODEL", "unit/short-fallback:free")
    monkeypatch.setattr(settings, "AI_SHORT_ANSWER_GRADING_TEMPERATURE", 0.1)
    monkeypatch.setattr(settings, "AI_SHORT_ANSWER_GRADING_MAX_TOKENS", 800)
    monkeypatch.setattr(settings, "AI_ESSAY_GRADING_PRIMARY_MODEL", "unit/essay-primary:free")
    monkeypatch.setattr(settings, "AI_ESSAY_GRADING_FALLBACK_MODEL", "unit/essay-fallback:free")
    monkeypatch.setattr(settings, "AI_ESSAY_GRADING_TEMPERATURE", 0.1)
    monkeypatch.setattr(settings, "AI_ESSAY_GRADING_MAX_TOKENS", 1600)


class FakeResponse:
    def __init__(self, payload: Any | None = None, *, status_code: int = 200, invalid_json: bool = False):
        self.payload = {} if payload is None else payload
        self.status_code = status_code
        self.invalid_json = invalid_json

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("POST", "https://openrouter.test/api/v1/chat/completions")
            raise httpx.HTTPStatusError("provider failed", request=request, response=self)

    def json(self) -> Any:
        if self.invalid_json:
            raise ValueError("not json")
        return self.payload


def _openrouter_payload(content: str = '{"ok": true}', model: str = PRIMARY) -> dict[str, Any]:
    return {
        "model": model,
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": 11, "completion_tokens": 7},
    }


def _set_short_answer_task(monkeypatch, *, primary: str = PRIMARY, fallback: str = FALLBACK) -> None:
    monkeypatch.setattr(settings, "AI_SHORT_ANSWER_GRADING_PRIMARY_MODEL", primary)
    monkeypatch.setattr(settings, "AI_SHORT_ANSWER_GRADING_FALLBACK_MODEL", fallback)
    monkeypatch.setattr(settings, "AI_SHORT_ANSWER_GRADING_TEMPERATURE", 0.35)
    monkeypatch.setattr(settings, "AI_SHORT_ANSWER_GRADING_MAX_TOKENS", 321)
    monkeypatch.setattr(settings, "AI_TIMEOUT_SECONDS", 23)
    monkeypatch.setattr(settings, "OPENROUTER_REQUIRE_FREE_MODELS", True)


def test_task_config_resolves_each_task(openrouter_settings) -> None:
    rubric = get_task_model_config(TASK_SUGGEST_ESSAY_RUBRIC)
    short = get_task_model_config(TASK_SHORT_ANSWER_GRADING)
    essay = get_task_model_config(TASK_ESSAY_GRADING)

    assert rubric.primary_model == "unit/rubric-primary:free"
    assert rubric.fallback_model == "unit/rubric-fallback:free"
    assert rubric.temperature == 0.2
    assert rubric.max_tokens == 1200
    assert short.primary_model == "unit/short-primary:free"
    assert short.fallback_model == "unit/short-fallback:free"
    assert short.temperature == 0.1
    assert short.max_tokens == 800
    assert essay.primary_model == "unit/essay-primary:free"
    assert essay.fallback_model == "unit/essay-fallback:free"
    assert essay.temperature == 0.1
    assert essay.max_tokens == 1600


def test_task_config_rejects_unsupported_task(openrouter_settings) -> None:
    with pytest.raises(AppException) as exc:
        get_task_model_config("unknown_task")

    assert exc.value.code == "AI_TASK_NOT_SUPPORTED"


def test_task_config_rejects_missing_primary(openrouter_settings, monkeypatch) -> None:
    monkeypatch.setattr(settings, "AI_SHORT_ANSWER_GRADING_PRIMARY_MODEL", "")

    with pytest.raises(AppException) as exc:
        get_task_model_config(TASK_SHORT_ANSWER_GRADING)

    assert exc.value.code == "AI_CONFIGURATION_ERROR"


def test_task_config_free_only_rejects_non_free_model(openrouter_settings, monkeypatch) -> None:
    monkeypatch.setattr(settings, "AI_SHORT_ANSWER_GRADING_PRIMARY_MODEL", "paid/model")

    with pytest.raises(AppException) as exc:
        get_task_model_config(TASK_SHORT_ANSWER_GRADING)

    assert exc.value.code == "AI_CONFIGURATION_ERROR"
    assert ":free" in exc.value.message


def test_task_config_can_allow_non_free_model(openrouter_settings, monkeypatch) -> None:
    monkeypatch.setattr(settings, "OPENROUTER_REQUIRE_FREE_MODELS", False)
    monkeypatch.setattr(settings, "AI_SHORT_ANSWER_GRADING_PRIMARY_MODEL", "paid/model")
    monkeypatch.setattr(settings, "AI_SHORT_ANSWER_GRADING_FALLBACK_MODEL", "paid/fallback")

    config = get_task_model_config(TASK_SHORT_ANSWER_GRADING)

    assert config.primary_model == "paid/model"
    assert config.fallback_model == "paid/fallback"


def test_task_config_validates_temperature_max_tokens_and_timeout(openrouter_settings, monkeypatch) -> None:
    monkeypatch.setattr(settings, "AI_SHORT_ANSWER_GRADING_TEMPERATURE", 2.1)
    with pytest.raises(AppException):
        get_task_model_config(TASK_SHORT_ANSWER_GRADING)

    monkeypatch.setattr(settings, "AI_SHORT_ANSWER_GRADING_TEMPERATURE", 0.1)
    monkeypatch.setattr(settings, "AI_SHORT_ANSWER_GRADING_MAX_TOKENS", 0)
    with pytest.raises(AppException):
        get_task_model_config(TASK_SHORT_ANSWER_GRADING)

    monkeypatch.setattr(settings, "AI_SHORT_ANSWER_GRADING_MAX_TOKENS", 800)
    monkeypatch.setattr(settings, "AI_TIMEOUT_SECONDS", 0)
    with pytest.raises(AppException):
        get_task_model_config(TASK_SHORT_ANSWER_GRADING)


def test_openrouter_missing_api_key_fails_before_http_call(openrouter_settings, monkeypatch) -> None:
    called = False

    def fake_post(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("HTTP must not be called without an API key.")

    monkeypatch.setattr("app.modules.ai.providers.httpx.post", fake_post)
    provider = OpenRouterProvider(api_key="")

    with pytest.raises(AppException) as exc:
        provider.generate_text(TASK_SHORT_ANSWER_GRADING, "prompt")

    assert exc.value.code == "AI_CONFIGURATION_ERROR"
    assert called is False


def test_openrouter_request_shape_and_response_normalization(openrouter_settings, monkeypatch) -> None:
    _set_short_answer_task(monkeypatch)
    calls: list[dict[str, Any]] = []

    def fake_post(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return FakeResponse(_openrouter_payload(model="unit/actual:free"))

    monkeypatch.setattr("app.modules.ai.providers.httpx.post", fake_post)
    provider = OpenRouterProvider(api_key="secret-value", base_url="https://openrouter.test/api/v1", site_url="")

    result = provider.generate_text(TASK_SHORT_ANSWER_GRADING, "grade this")

    assert calls[0]["url"] == "https://openrouter.test/api/v1/chat/completions"
    assert calls[0]["headers"]["Authorization"] == "Bearer secret-value"
    assert calls[0]["headers"]["Content-Type"] == "application/json"
    assert "HTTP-Referer" not in calls[0]["headers"]
    assert calls[0]["headers"]["X-Title"] == "Unit Test App"
    assert calls[0]["json"]["models"] == [PRIMARY, FALLBACK]
    assert "model" not in calls[0]["json"]
    assert calls[0]["json"]["response_format"] == {"type": "json_object"}
    assert calls[0]["json"]["provider"] == {"require_parameters": True}
    assert calls[0]["json"]["temperature"] == 0.35
    assert calls[0]["json"]["max_tokens"] == 321
    assert calls[0]["timeout"] == 23
    assert result.provider == "openrouter"
    assert result.model == "unit/actual:free"
    assert result.prompt_tokens == 11
    assert result.completion_tokens == 7
    assert result.response_json == {"ok": True}


def test_openrouter_uses_primary_model_when_response_model_is_omitted(openrouter_settings, monkeypatch) -> None:
    _set_short_answer_task(monkeypatch)
    payload = _openrouter_payload()
    payload.pop("model")
    monkeypatch.setattr("app.modules.ai.providers.httpx.post", lambda *args, **kwargs: FakeResponse(payload))

    result = OpenRouterProvider(api_key="secret-value").generate_text(TASK_SHORT_ANSWER_GRADING, "prompt")

    assert result.model == PRIMARY


def test_openrouter_includes_optional_referer_when_configured(openrouter_settings, monkeypatch) -> None:
    _set_short_answer_task(monkeypatch)

    def fake_post(url, **kwargs):
        assert kwargs["headers"]["HTTP-Referer"] == "https://example.test"
        return FakeResponse(_openrouter_payload())

    monkeypatch.setattr("app.modules.ai.providers.httpx.post", fake_post)
    provider = OpenRouterProvider(api_key="secret-value", site_url="https://example.test")

    provider.generate_text(TASK_SHORT_ANSWER_GRADING, "prompt")


def test_openrouter_omits_optional_title_when_blank(openrouter_settings, monkeypatch) -> None:
    _set_short_answer_task(monkeypatch)

    def fake_post(url, **kwargs):
        assert "X-Title" not in kwargs["headers"]
        return FakeResponse(_openrouter_payload())

    monkeypatch.setattr("app.modules.ai.providers.httpx.post", fake_post)
    provider = OpenRouterProvider(api_key="secret-value", app_name="")

    provider.generate_text(TASK_SHORT_ANSWER_GRADING, "prompt")


def test_openrouter_duplicate_fallback_model_is_sent_once(openrouter_settings, monkeypatch) -> None:
    _set_short_answer_task(monkeypatch, primary=PRIMARY, fallback=PRIMARY)

    def fake_post(url, **kwargs):
        assert kwargs["json"]["models"] == [PRIMARY]
        return FakeResponse(_openrouter_payload(model=PRIMARY))

    monkeypatch.setattr("app.modules.ai.providers.httpx.post", fake_post)

    OpenRouterProvider(api_key="secret-value").generate_text(TASK_SHORT_ANSWER_GRADING, "prompt")


def test_openrouter_safe_http_error_does_not_expose_secret(openrouter_settings, monkeypatch) -> None:
    _set_short_answer_task(monkeypatch)

    def fake_post(url, **kwargs):
        return FakeResponse(status_code=500)

    monkeypatch.setattr("app.modules.ai.providers.httpx.post", fake_post)

    with pytest.raises(AppException) as exc:
        OpenRouterProvider(api_key="super-secret-key").generate_text(TASK_SHORT_ANSWER_GRADING, "prompt")

    assert "super-secret-key" not in exc.value.message
    assert "Authorization" not in exc.value.message


def test_openrouter_timeout_fails_safely_without_secret(openrouter_settings, monkeypatch) -> None:
    _set_short_answer_task(monkeypatch)

    def fake_post(url, **kwargs):
        raise httpx.TimeoutException("timed out with secret-value")

    monkeypatch.setattr("app.modules.ai.providers.httpx.post", fake_post)

    with pytest.raises(AppException) as exc:
        OpenRouterProvider(api_key="secret-value").generate_text(TASK_SHORT_ANSWER_GRADING, "prompt")

    assert exc.value.code == "AI_PROVIDER_ERROR"
    assert exc.value.message == "AI provider request failed."
    assert exc.value.details == {"provider": "openrouter", "error": "timeout"}
    assert "secret-value" not in exc.value.message


def test_openrouter_invalid_http_json_fails_safely(openrouter_settings, monkeypatch) -> None:
    _set_short_answer_task(monkeypatch)
    monkeypatch.setattr("app.modules.ai.providers.httpx.post", lambda *args, **kwargs: FakeResponse(invalid_json=True))

    with pytest.raises(AppException) as exc:
        OpenRouterProvider(api_key="secret-value").generate_text(TASK_SHORT_ANSWER_GRADING, "prompt")

    assert exc.value.code == "AI_PROVIDER_ERROR"
    assert exc.value.message == "AI provider request failed."
    assert exc.value.details == {"provider": "openrouter", "error": "invalid_provider_json"}


def test_openrouter_non_object_http_json_fails_safely(openrouter_settings, monkeypatch) -> None:
    _set_short_answer_task(monkeypatch)
    monkeypatch.setattr("app.modules.ai.providers.httpx.post", lambda *args, **kwargs: FakeResponse([]))

    with pytest.raises(AppException) as exc:
        OpenRouterProvider(api_key="secret-value").generate_text(TASK_SHORT_ANSWER_GRADING, "prompt")

    assert exc.value.code == "AI_PROVIDER_ERROR"
    assert exc.value.message == "AI provider request failed."
    assert exc.value.details == {"provider": "openrouter", "error": "invalid_provider_json"}


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"choices": []},
        {"choices": [{"message": {}}]},
        {"choices": [{"message": {"content": "   "}}]},
    ],
)
def test_openrouter_malformed_provider_response_fails_safely(openrouter_settings, monkeypatch, payload) -> None:
    _set_short_answer_task(monkeypatch)
    monkeypatch.setattr("app.modules.ai.providers.httpx.post", lambda *args, **kwargs: FakeResponse(payload))

    with pytest.raises(AppException) as exc:
        OpenRouterProvider(api_key="secret-value").generate_text(TASK_SHORT_ANSWER_GRADING, "prompt")

    assert exc.value.code == "AI_PROVIDER_ERROR"


def test_openrouter_ignores_malformed_usage(openrouter_settings, monkeypatch) -> None:
    _set_short_answer_task(monkeypatch)
    payload = _openrouter_payload()
    payload["usage"] = "not-a-dict"
    monkeypatch.setattr("app.modules.ai.providers.httpx.post", lambda *args, **kwargs: FakeResponse(payload))

    result = OpenRouterProvider(api_key="secret-value").generate_text(TASK_SHORT_ANSWER_GRADING, "prompt")

    assert result.prompt_tokens is None
    assert result.completion_tokens is None


def test_openrouter_invalid_json_retries_once_with_fallback(openrouter_settings, monkeypatch) -> None:
    _set_short_answer_task(monkeypatch)
    calls: list[dict[str, Any]] = []
    responses = [
        FakeResponse(_openrouter_payload(content="not json", model=PRIMARY)),
        FakeResponse(_openrouter_payload(content='{"ok": true}', model=FALLBACK)),
    ]

    def fake_post(url, **kwargs):
        calls.append(kwargs["json"])
        return responses.pop(0)

    monkeypatch.setattr("app.modules.ai.providers.httpx.post", fake_post)

    result = OpenRouterProvider(api_key="secret-value").generate_text(TASK_SHORT_ANSWER_GRADING, "prompt")

    assert len(calls) == 2
    assert calls[0]["models"] == [PRIMARY, FALLBACK]
    assert calls[1]["models"] == [FALLBACK]
    assert result.model == FALLBACK
    assert result.response_json == {"ok": True}


def test_openrouter_valid_primary_json_does_not_retry(openrouter_settings, monkeypatch) -> None:
    _set_short_answer_task(monkeypatch)
    calls = 0

    def fake_post(url, **kwargs):
        nonlocal calls
        calls += 1
        return FakeResponse(_openrouter_payload(content='{"ok": true}', model=PRIMARY))

    monkeypatch.setattr("app.modules.ai.providers.httpx.post", fake_post)

    OpenRouterProvider(api_key="secret-value").generate_text(TASK_SHORT_ANSWER_GRADING, "prompt")

    assert calls == 1


def test_openrouter_invalid_fallback_json_fails_without_loop(openrouter_settings, monkeypatch) -> None:
    _set_short_answer_task(monkeypatch)
    calls = 0

    def fake_post(url, **kwargs):
        nonlocal calls
        calls += 1
        model = PRIMARY if calls == 1 else FALLBACK
        return FakeResponse(_openrouter_payload(content="not json", model=model))

    monkeypatch.setattr("app.modules.ai.providers.httpx.post", fake_post)

    with pytest.raises(AppException) as exc:
        OpenRouterProvider(api_key="secret-value").generate_text(TASK_SHORT_ANSWER_GRADING, "prompt")

    assert exc.value.code == "AI_PROVIDER_ERROR"
    assert calls == 2


def test_build_provider_supports_openrouter(openrouter_settings) -> None:
    assert isinstance(build_provider(), OpenRouterProvider)


def test_mock_provider_remains_deterministic() -> None:
    provider = MockProvider()

    first = provider.generate_text(
        TASK_SHORT_ANSWER_GRADING,
        "prompt",
        metadata={"student_answer": "answer", "max_score": 5},
    )
    second = provider.generate_text(
        TASK_SHORT_ANSWER_GRADING,
        "prompt",
        metadata={"student_answer": "answer", "max_score": 5},
    )

    assert first.text == second.text
    assert first.model == "mock"


def test_gemini_provider_remains_compatible(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []

    def fake_post(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return FakeResponse(
            {
                "candidates": [{"content": {"parts": [{"text": '{"ok": true}'}]}}],
                "usageMetadata": {"promptTokenCount": 3, "candidatesTokenCount": 4},
            }
        )

    monkeypatch.setattr("app.modules.ai.providers.httpx.post", fake_post)
    provider = GeminiProvider(api_key="gemini-key", model="gemini-test", timeout_seconds=9)

    result = provider.generate_text(TASK_SHORT_ANSWER_GRADING, "prompt")

    assert calls[0]["url"].endswith("/models/gemini-test:generateContent")
    assert calls[0]["params"] == {"key": "gemini-key"}
    assert calls[0]["timeout"] == 9
    assert result.provider == "gemini"
    assert result.model == "gemini-test"


def test_gemini_provider_http_error_does_not_expose_key(monkeypatch) -> None:
    def fake_post(url, **kwargs):
        response = FakeResponse(status_code=403)
        request = httpx.Request("POST", f"{url}?key=super-secret-gemini-key")
        raise httpx.HTTPStatusError("failed url includes key=super-secret-gemini-key", request=request, response=response)

    monkeypatch.setattr("app.modules.ai.providers.httpx.post", fake_post)
    provider = GeminiProvider(api_key="super-secret-gemini-key", model="gemini-test", timeout_seconds=9)

    with pytest.raises(AppException) as exc:
        provider.generate_text(TASK_SHORT_ANSWER_GRADING, "prompt")

    assert exc.value.code == "AI_PROVIDER_ERROR"
    assert exc.value.message == "AI provider request failed."
    assert exc.value.details == {"provider": "gemini", "status_code": 403}
    assert "super-secret-gemini-key" not in exc.value.message
    assert "key=" not in exc.value.message


def test_gateway_callers_do_not_need_task_model_arguments() -> None:
    class Provider:
        name = "fake"
        model = "fake-model"

        def generate_text(self, task_name, prompt, response_schema=None, metadata=None):
            assert task_name == TASK_SHORT_ANSWER_GRADING
            assert response_schema is None
            assert metadata == {"answer": "x"}
            return GatewayResult(text='{"ok": true}', provider=self.name, model=self.model)

    result = ModelGateway(provider=Provider()).run(TASK_SHORT_ANSWER_GRADING, {"answer": "x"})

    assert result.provider == "fake"


def test_ai_service_openrouter_success_logs_actual_model(openrouter_settings, monkeypatch) -> None:
    logs = []

    class Repository:
        def create_log(self, log):
            logs.append(log)
            return log

        def rollback(self):
            pass

    class Gateway:
        def generate(self, **kwargs):
            return GatewayResult(
                text='{"criteria": [{"name": "Accuracy", "description": "Correct", "points": 5}], "total_points": 5}',
                provider="openrouter",
                model=FALLBACK,
                raw_response="{}",
                response_json={"criteria": [{"name": "Accuracy", "description": "Correct", "points": 5}], "total_points": 5},
            )

    service = AIService(db=None, gateway=Gateway())
    service.repository = Repository()

    service.suggest_essay_rubric("Question?", "Answer.", Decimal("5"), AICallContext())

    assert logs[0].provider == "openrouter"
    assert logs[0].model == FALLBACK


def test_ai_service_openrouter_failure_logs_primary_without_secret(openrouter_settings, monkeypatch) -> None:
    monkeypatch.setattr(settings, "AI_SHORT_ANSWER_GRADING_PRIMARY_MODEL", PRIMARY)
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "do-not-log")
    logs = []

    class Repository:
        def create_log(self, log):
            logs.append(log)
            return log

        def rollback(self):
            pass

    class Gateway:
        def run(self, task_name, payload):
            raise AppException(code="AI_PROVIDER_ERROR", message="OpenRouter request failed.", status_code=502)

    service = AIService(db=None, gateway=Gateway())
    service.repository = Repository()

    with pytest.raises(AppException):
        service.grade_subjective_answer(
            task_name=TASK_SHORT_ANSWER_GRADING,
            payload={"student_answer": "x"},
            max_score=Decimal("5"),
            context=AICallContext(),
        )

    assert logs[0].provider == "openrouter"
    assert logs[0].model == PRIMARY
    assert "do-not-log" not in str(logs[0].request_json)
    assert "do-not-log" not in (logs[0].error_message or "")
