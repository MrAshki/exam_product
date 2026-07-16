import json
from decimal import Decimal
from typing import Any, Protocol

import httpx

from app.core.config import settings
from app.core.exceptions import AppException
from app.modules.ai.errors import ai_configuration_error, ai_provider_error, ai_task_not_supported
from app.modules.ai.parser import parse_rubric_response
from app.modules.ai.schemas import GatewayResult


class Provider(Protocol):
    name: str
    model: str

    def generate_text(
        self,
        task_name: str,
        prompt: str,
        response_schema: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GatewayResult:
        ...


class MockProvider:
    name = "mock"

    def __init__(self, model: str = "mock") -> None:
        self.model = model

    def generate_text(
        self,
        task_name: str,
        prompt: str,
        response_schema: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GatewayResult:
        if task_name in {"short_answer_grading", "essay_grading"}:
            max_score = float((metadata or {}).get("max_score") or (metadata or {}).get("points") or 0)
            student_answer = str((metadata or {}).get("student_answer") or "").strip()
            score = max_score if student_answer else 0.0
            response = {
                "score": score,
                "feedback": "Mock AI grading feedback.",
                "confidence": 0.9 if student_answer else 0.5,
                "needs_review": False if student_answer else True,
            }
            text = json.dumps(response)
            return GatewayResult(
                text=text,
                provider=self.name,
                model=self.model,
                raw_response=text,
                response_json=response,
            )

        if task_name != "suggest_essay_rubric":
            raise ai_task_not_supported(task_name)
        total_points = Decimal(str((metadata or {}).get("total_points") or "10"))
        if total_points <= Decimal("1"):
            criteria = [
                {
                    "name": "Accuracy",
                    "description": "Correctness of the answer",
                    "points": float(total_points),
                }
            ]
        else:
            accuracy_points = max(Decimal("0.01"), (total_points * Decimal("0.6")).quantize(Decimal("0.01")))
            clarity_points = total_points - accuracy_points
            if clarity_points <= 0:
                accuracy_points = total_points - Decimal("0.01")
                clarity_points = Decimal("0.01")
            criteria = [
                {
                    "name": "Accuracy",
                    "description": "Correctness of the answer",
                    "points": float(accuracy_points),
                },
                {
                    "name": "Clarity",
                    "description": "Clear explanation",
                    "points": float(clarity_points),
                },
            ]
        rubric = {"criteria": criteria, "total_points": float(total_points)}
        text = json.dumps(rubric)
        return GatewayResult(
            text=text,
            provider=self.name,
            model=self.model,
            raw_response=text,
            response_json=rubric,
        )


class GeminiProvider:
    name = "gemini"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.AI_MODEL
        self.timeout_seconds = timeout_seconds or settings.AI_TIMEOUT_SECONDS
        if not self.api_key:
            raise ai_configuration_error("GEMINI_API_KEY is required when AI_PROVIDER=gemini.")

    def generate_text(
        self,
        task_name: str,
        prompt: str,
        response_schema: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GatewayResult:
        if task_name not in {"suggest_essay_rubric", "short_answer_grading", "essay_grading"}:
            raise ai_task_not_supported(task_name)

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )
        body = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt,
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
            },
        }

        try:
            response = httpx.post(
                url,
                params={"key": self.api_key},
                json=body,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            response_json = response.json()
        except httpx.TimeoutException as exc:
            raise ai_provider_error(
                "AI provider request failed.",
                details={"provider": self.name, "error": "timeout"},
            ) from exc
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            raise ai_provider_error(
                "AI provider request failed.",
                details={"provider": self.name, "status_code": status_code},
            ) from exc
        except httpx.HTTPError as exc:
            raise ai_provider_error(
                "AI provider request failed.",
                details={"provider": self.name, "error": "http_error"},
            ) from exc
        except ValueError as exc:
            raise ai_provider_error("Gemini response was not valid JSON.") from exc

        try:
            text = response_json["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ai_provider_error("Gemini response did not include text output.") from exc

        usage = response_json.get("usageMetadata") or {}
        return GatewayResult(
            text=text,
            provider=self.name,
            model=self.model,
            raw_response=json.dumps(response_json),
            response_json=response_json,
            prompt_tokens=usage.get("promptTokenCount"),
            completion_tokens=usage.get("candidatesTokenCount"),
        )


class OpenRouterProvider:
    name = "openrouter"
    model = "task-configured"

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        site_url: str | None = None,
        app_name: str | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.OPENROUTER_API_KEY
        self.base_url = (base_url if base_url is not None else settings.OPENROUTER_BASE_URL).rstrip("/")
        self.site_url = site_url if site_url is not None else settings.OPENROUTER_SITE_URL
        self.app_name = app_name if app_name is not None else settings.OPENROUTER_APP_NAME

    def generate_text(
        self,
        task_name: str,
        prompt: str,
        response_schema: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GatewayResult:
        from app.modules.ai.task_config import JSON_OBJECT_RESPONSE_FORMAT, get_task_model_config

        if not self.api_key:
            raise ai_configuration_error("OPENROUTER_API_KEY is required when AI_PROVIDER=openrouter.")
        if not self.base_url:
            raise ai_configuration_error("OPENROUTER_BASE_URL is required when AI_PROVIDER=openrouter.")

        task_config = get_task_model_config(task_name)
        has_distinct_fallback = bool(task_config.fallback_model and task_config.fallback_model != task_config.primary_model)
        result = self._request_completion_with_optional_fallback(
            prompt=prompt,
            task_config=task_config,
            has_distinct_fallback=has_distinct_fallback,
        )

        if task_config.response_format == JSON_OBJECT_RESPONSE_FORMAT:
            parsed = self._parse_json_content(result.text)
            if parsed is None:
                return self._retry_fallback_for_invalid_content(
                    prompt=prompt,
                    task_config=task_config,
                    response_schema=response_schema,
                    metadata=metadata,
                    has_distinct_fallback=has_distinct_fallback,
                    actual_model=result.model,
                    error=ai_provider_error(
                        "AI provider request failed.",
                        details={"provider": self.name, "error": "invalid_json"},
                    ),
                )
            result.response_json = parsed
            schema_error = self._validate_response_schema(response_schema, result.text, metadata)
            if schema_error is not None:
                return self._retry_fallback_for_invalid_content(
                    prompt=prompt,
                    task_config=task_config,
                    response_schema=response_schema,
                    metadata=metadata,
                    has_distinct_fallback=has_distinct_fallback,
                    actual_model=result.model,
                    error=schema_error,
                )

        return result

    def _request_completion_with_optional_fallback(
        self,
        *,
        prompt: str,
        task_config: Any,
        has_distinct_fallback: bool,
    ) -> GatewayResult:
        try:
            return self._request_completion(
                prompt=prompt,
                models=self._ordered_models(task_config.primary_model, task_config.fallback_model),
                task_config=task_config,
            )
        except AppException as exc:
            if exc.code != "AI_PROVIDER_ERROR" or not has_distinct_fallback:
                raise
            return self._request_completion(
                prompt=prompt,
                models=[task_config.fallback_model],
                task_config=task_config,
            )

    def _retry_fallback_for_invalid_content(
        self,
        *,
        prompt: str,
        task_config: Any,
        response_schema: dict[str, Any] | None,
        metadata: dict[str, Any] | None,
        has_distinct_fallback: bool,
        actual_model: str | None,
        error: AppException,
    ) -> GatewayResult:
        if not has_distinct_fallback or actual_model == task_config.fallback_model:
            raise error

        fallback_result = self._request_completion(
            prompt=prompt,
            models=[task_config.fallback_model],
            task_config=task_config,
        )
        fallback_parsed = self._parse_json_content(fallback_result.text)
        if fallback_parsed is None:
            raise ai_provider_error(
                "AI provider request failed.",
                details={"provider": self.name, "error": "invalid_json"},
            )
        fallback_result.response_json = fallback_parsed
        fallback_schema_error = self._validate_response_schema(response_schema, fallback_result.text, metadata)
        if fallback_schema_error is not None:
            raise fallback_schema_error
        return fallback_result

    def _request_completion(
        self,
        *,
        prompt: str,
        models: list[str],
        task_config: Any,
    ) -> GatewayResult:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.app_name:
            headers["X-Title"] = self.app_name

        body = {
            "models": models,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": task_config.temperature,
            "max_tokens": task_config.max_tokens,
            "response_format": {"type": task_config.response_format},
            "provider": {"require_parameters": True},
            "stream": False,
        }

        try:
            response = httpx.post(
                url,
                headers=headers,
                json=body,
                timeout=task_config.timeout_seconds,
            )
            response.raise_for_status()
            response_json = response.json()
        except httpx.TimeoutException as exc:
            raise ai_provider_error(
                "AI provider request failed.",
                details={"provider": self.name, "error": "timeout"},
            ) from exc
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            raise ai_provider_error(
                "AI provider request failed.",
                details={"provider": self.name, "status_code": status_code},
            ) from exc
        except httpx.HTTPError as exc:
            raise ai_provider_error(
                "AI provider request failed.",
                details={"provider": self.name, "error": "http_error"},
            ) from exc
        except ValueError as exc:
            raise ai_provider_error(
                "AI provider request failed.",
                details={"provider": self.name, "error": "invalid_provider_json"},
            ) from exc

        if not isinstance(response_json, dict):
            raise ai_provider_error(
                "AI provider request failed.",
                details={"provider": self.name, "error": "invalid_provider_json"},
            )

        try:
            choice = response_json["choices"][0]
            message = choice["message"]
            text = message["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ai_provider_error(
                "AI provider request failed.",
                details={"provider": self.name, "error": "missing_text"},
            ) from exc
        if not isinstance(text, str) or not text.strip():
            raise ai_provider_error(
                "AI provider request failed.",
                details={"provider": self.name, "error": "empty_text"},
            )

        usage = response_json.get("usage") or {}
        if not isinstance(usage, dict):
            usage = {}
        actual_model = response_json.get("model") or task_config.primary_model
        return GatewayResult(
            text=text,
            provider=self.name,
            model=actual_model,
            raw_response=json.dumps(response_json),
            response_json=response_json if isinstance(response_json, dict) else None,
            prompt_tokens=self._int_or_none(usage.get("prompt_tokens")),
            completion_tokens=self._int_or_none(usage.get("completion_tokens")),
        )

    @staticmethod
    def _ordered_models(primary_model: str, fallback_model: str | None) -> list[str]:
        primary = primary_model.strip()
        fallback = fallback_model.strip() if fallback_model else None
        if fallback and fallback != primary:
            return [primary, fallback]
        return [primary]

    @staticmethod
    def _parse_json_content(text: str) -> dict[str, Any] | list[Any] | None:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, (dict, list)):
            return parsed
        return None

    @staticmethod
    def _validate_response_schema(
        response_schema: dict[str, Any] | None,
        text: str,
        metadata: dict[str, Any] | None,
    ) -> AppException | None:
        if not response_schema or response_schema.get("type") != "rubric":
            return None
        try:
            total_points = Decimal(str((metadata or {}).get("total_points")))
            parse_rubric_response(text, total_points)
        except AppException as exc:
            return exc
        return None

    @staticmethod
    def _int_or_none(value: Any) -> int | None:
        return value if isinstance(value, int) and not isinstance(value, bool) else None


def build_provider() -> Provider:
    provider = settings.AI_PROVIDER.lower()
    if provider == "mock":
        return MockProvider(model="mock")
    if provider == "gemini":
        return GeminiProvider()
    if provider == "openrouter":
        return OpenRouterProvider()
    raise ai_configuration_error(f"Unsupported AI_PROVIDER: {settings.AI_PROVIDER}.")
