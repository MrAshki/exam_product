from dataclasses import dataclass
from typing import Final

from app.core.config import settings
from app.modules.ai.errors import ai_configuration_error, ai_task_not_supported


TASK_SUGGEST_ESSAY_RUBRIC: Final = "suggest_essay_rubric"
TASK_SHORT_ANSWER_GRADING: Final = "short_answer_grading"
TASK_ESSAY_GRADING: Final = "essay_grading"
JSON_OBJECT_RESPONSE_FORMAT: Final = "json_object"


@dataclass(frozen=True)
class TaskModelConfig:
    task_name: str
    primary_model: str
    fallback_model: str | None
    temperature: float
    max_tokens: int
    timeout_seconds: int
    response_format: str


def get_task_model_config(task_name: str) -> TaskModelConfig:
    if task_name == TASK_SUGGEST_ESSAY_RUBRIC:
        config = TaskModelConfig(
            task_name=task_name,
            primary_model=settings.AI_SUGGEST_ESSAY_RUBRIC_PRIMARY_MODEL.strip(),
            fallback_model=_clean_optional(settings.AI_SUGGEST_ESSAY_RUBRIC_FALLBACK_MODEL),
            temperature=settings.AI_SUGGEST_ESSAY_RUBRIC_TEMPERATURE,
            max_tokens=settings.AI_SUGGEST_ESSAY_RUBRIC_MAX_TOKENS,
            timeout_seconds=settings.AI_TIMEOUT_SECONDS,
            response_format=JSON_OBJECT_RESPONSE_FORMAT,
        )
    elif task_name == TASK_SHORT_ANSWER_GRADING:
        config = TaskModelConfig(
            task_name=task_name,
            primary_model=settings.AI_SHORT_ANSWER_GRADING_PRIMARY_MODEL.strip(),
            fallback_model=_clean_optional(settings.AI_SHORT_ANSWER_GRADING_FALLBACK_MODEL),
            temperature=settings.AI_SHORT_ANSWER_GRADING_TEMPERATURE,
            max_tokens=settings.AI_SHORT_ANSWER_GRADING_MAX_TOKENS,
            timeout_seconds=settings.AI_TIMEOUT_SECONDS,
            response_format=JSON_OBJECT_RESPONSE_FORMAT,
        )
    elif task_name == TASK_ESSAY_GRADING:
        config = TaskModelConfig(
            task_name=task_name,
            primary_model=settings.AI_ESSAY_GRADING_PRIMARY_MODEL.strip(),
            fallback_model=_clean_optional(settings.AI_ESSAY_GRADING_FALLBACK_MODEL),
            temperature=settings.AI_ESSAY_GRADING_TEMPERATURE,
            max_tokens=settings.AI_ESSAY_GRADING_MAX_TOKENS,
            timeout_seconds=settings.AI_TIMEOUT_SECONDS,
            response_format=JSON_OBJECT_RESPONSE_FORMAT,
        )
    else:
        raise ai_task_not_supported(task_name)

    _validate_config(config)
    return config


def supported_task_names() -> tuple[str, ...]:
    return (
        TASK_SUGGEST_ESSAY_RUBRIC,
        TASK_SHORT_ANSWER_GRADING,
        TASK_ESSAY_GRADING,
    )


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _validate_config(config: TaskModelConfig) -> None:
    primary_model = config.primary_model.strip()
    if not primary_model:
        raise ai_configuration_error(f"Primary model is required for AI task {config.task_name}.")
    if config.timeout_seconds <= 0:
        raise ai_configuration_error("AI_TIMEOUT_SECONDS must be positive.")
    if config.max_tokens <= 0:
        raise ai_configuration_error(f"Max tokens must be positive for AI task {config.task_name}.")
    if config.temperature < 0 or config.temperature > 2:
        raise ai_configuration_error(f"Temperature must be between 0 and 2 for AI task {config.task_name}.")

    if settings.OPENROUTER_REQUIRE_FREE_MODELS:
        _require_free_model(primary_model, config.task_name, "primary")
        if config.fallback_model:
            _require_free_model(config.fallback_model, config.task_name, "fallback")


def _require_free_model(model: str, task_name: str, role: str) -> None:
    if not model.endswith(":free"):
        raise ai_configuration_error(
            f"OpenRouter {role} model for AI task {task_name} must end with :free "
            "when OPENROUTER_REQUIRE_FREE_MODELS=true."
        )
