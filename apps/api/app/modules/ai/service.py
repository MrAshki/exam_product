import hashlib
import json
import time
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AppException
from app.modules.ai.errors import ai_provider_error
from app.modules.ai.gateway import ModelGateway
from app.modules.ai.logs import AILog
from app.modules.ai.parser import parse_grading_response, parse_rubric_response
from app.modules.ai.prompts import build_suggest_essay_rubric_prompt
from app.modules.ai.repository import AIRepository
from app.modules.ai.schemas import AICallContext


class AIService:
    def __init__(self, db: Session, gateway: ModelGateway | None = None) -> None:
        self.repository = AIRepository(db)
        self.gateway = gateway

    def suggest_essay_rubric(
        self,
        question_text: str,
        expected_answer: str,
        total_points: Decimal,
        context: AICallContext,
    ) -> dict[str, Any]:
        task_name = "suggest_essay_rubric"
        prompt = build_suggest_essay_rubric_prompt(
            question_text=question_text,
            expected_answer=expected_answer,
            total_points=total_points,
        )
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        started_at = time.perf_counter()
        provider = settings.AI_PROVIDER.lower()
        model = settings.AI_MODEL
        request_json = {
            "task_name": task_name,
            "prompt_hash": prompt_hash,
            "metadata": {"total_points": total_points},
        }

        try:
            gateway = self.gateway or ModelGateway()
            result = gateway.generate(
                task_name=task_name,
                prompt=prompt,
                response_schema={"type": "rubric"},
                metadata={"total_points": total_points},
            )
            rubric = parse_rubric_response(result.text, total_points)
            self._log(
                context=context,
                task_name=task_name,
                provider=result.provider,
                model=result.model,
                status="success",
                prompt_hash=prompt_hash,
                request_json=request_json,
                response_json=result.response_json or rubric,
                raw_response=result.raw_response,
                latency_ms=self._latency_ms(started_at),
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
            )
            return rubric
        except AppException as exc:
            self._log(
                context=context,
                task_name=task_name,
                provider=provider,
                model=model,
                status="failed",
                prompt_hash=prompt_hash,
                request_json=request_json,
                error_code=exc.code,
                error_message=exc.message,
                latency_ms=self._latency_ms(started_at),
            )
            raise

    def grade_subjective_answer(
        self,
        *,
        task_name: str,
        payload: dict[str, Any],
        max_score: Decimal,
        context: AICallContext,
    ) -> dict[str, Any]:
        request_payload = json.loads(json.dumps(payload, sort_keys=True, default=str))
        payload_text = json.dumps(request_payload, sort_keys=True)
        prompt_hash = hashlib.sha256(payload_text.encode("utf-8")).hexdigest()
        started_at = time.perf_counter()
        provider = settings.AI_PROVIDER.lower()
        model = settings.AI_MODEL
        request_json = {
            "task_name": task_name,
            "prompt_hash": prompt_hash,
            "payload": request_payload,
        }

        try:
            gateway = self.gateway or ModelGateway()
            result = gateway.run(task_name, request_payload)
            grading = parse_grading_response(result.text, max_score)
            self._log(
                context=context,
                task_name=task_name,
                provider=result.provider,
                model=result.model,
                status="success",
                prompt_hash=prompt_hash,
                request_json=request_json,
                response_json=result.response_json or self._json_safe(grading),
                raw_response=result.raw_response,
                latency_ms=self._latency_ms(started_at),
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
            )
            return grading
        except AppException as exc:
            self._log(
                context=context,
                task_name=task_name,
                provider=provider,
                model=model,
                status="failed",
                prompt_hash=prompt_hash,
                request_json=request_json,
                error_code=exc.code,
                error_message=exc.message,
                latency_ms=self._latency_ms(started_at),
            )
            raise
        except Exception as exc:
            error = ai_provider_error(str(exc))
            self._log(
                context=context,
                task_name=task_name,
                provider=provider,
                model=model,
                status="failed",
                prompt_hash=prompt_hash,
                request_json=request_json,
                error_code=error.code,
                error_message=error.message,
                latency_ms=self._latency_ms(started_at),
            )
            raise error from exc

    def _log(
        self,
        context: AICallContext,
        task_name: str,
        provider: str,
        model: str,
        status: str,
        prompt_hash: str | None = None,
        request_json: dict[str, Any] | None = None,
        response_json: dict[str, Any] | None = None,
        raw_response: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        latency_ms: int | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
    ) -> None:
        log = AILog(
            teacher_id=context.teacher_id,
            class_id=context.class_id,
            exam_id=context.exam_id,
            question_id=context.question_id,
            task_name=task_name,
            provider=provider,
            model=model,
            status=status,
            prompt_hash=prompt_hash,
            request_json=request_json,
            response_json=response_json,
            raw_response=raw_response,
            error_code=error_code,
            error_message=error_message,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        try:
            self.repository.create_log(log)
        except Exception:
            self.repository.rollback()

    @staticmethod
    def _latency_ms(started_at: float) -> int:
        return int((time.perf_counter() - started_at) * 1000)

    @staticmethod
    def _json_safe(payload: dict[str, Any]) -> dict[str, Any]:
        return json.loads(json.dumps(payload, default=str))
