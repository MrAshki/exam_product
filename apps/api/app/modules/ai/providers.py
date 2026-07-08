import json
from typing import Any, Protocol

import httpx

from app.core.config import settings
from app.modules.ai.errors import ai_configuration_error, ai_provider_error, ai_task_not_supported
from app.modules.ai.schemas import GatewayResult


class Provider(Protocol):
    name: str
    model: str

    def generate_text(
        self,
        task_name: str,
        prompt: str,
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
        total_points = int((metadata or {}).get("total_points") or 10)
        if total_points <= 1:
            criteria = [
                {
                    "name": "Accuracy",
                    "description": "Correctness of the answer",
                    "points": total_points,
                }
            ]
        else:
            accuracy_points = max(1, round(total_points * 0.6))
            clarity_points = total_points - accuracy_points
            if clarity_points <= 0:
                accuracy_points = total_points - 1
                clarity_points = 1
            criteria = [
                {
                    "name": "Accuracy",
                    "description": "Correctness of the answer",
                    "points": accuracy_points,
                },
                {
                    "name": "Clarity",
                    "description": "Clear explanation",
                    "points": clarity_points,
                },
            ]
        rubric = {"criteria": criteria, "total_points": total_points}
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
        except httpx.HTTPError as exc:
            raise ai_provider_error(str(exc)) from exc
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


def build_provider() -> Provider:
    provider = settings.AI_PROVIDER.lower()
    if provider == "mock":
        return MockProvider(model="mock")
    if provider == "gemini":
        return GeminiProvider()
    raise ai_configuration_error(f"Unsupported AI_PROVIDER: {settings.AI_PROVIDER}.")
