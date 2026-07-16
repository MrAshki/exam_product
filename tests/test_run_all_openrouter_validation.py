from __future__ import annotations

from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "scripts" / "dev" / "run-all.ps1"


def _runner_text() -> str:
    return RUNNER.read_text(encoding="utf-8")


def test_runner_accepts_openrouter_provider() -> None:
    text = _runner_text()

    assert 'SUPPORTED_AI = {"mock", "gemini", "openrouter"}' in text


def test_runner_clears_openrouter_process_overrides_for_configured_mode() -> None:
    text = _runner_text()

    for key in [
        "OPENROUTER_API_KEY",
        "OPENROUTER_BASE_URL",
        "OPENROUTER_SITE_URL",
        "OPENROUTER_APP_NAME",
        "OPENROUTER_REQUIRE_FREE_MODELS",
        "AI_SUGGEST_ESSAY_RUBRIC_PRIMARY_MODEL",
        "AI_SUGGEST_ESSAY_RUBRIC_FALLBACK_MODEL",
        "AI_SHORT_ANSWER_GRADING_PRIMARY_MODEL",
        "AI_SHORT_ANSWER_GRADING_FALLBACK_MODEL",
        "AI_ESSAY_GRADING_PRIMARY_MODEL",
        "AI_ESSAY_GRADING_FALLBACK_MODEL",
    ]:
        assert f'"{key}"' in text


def test_runner_openrouter_validation_is_safe_and_strict() -> None:
    text = _runner_text()

    assert 'require(bool(settings.OPENROUTER_API_KEY), "OPENROUTER_API_KEY is required for AI_PROVIDER=openrouter")' in text
    assert 'require(bool(settings.OPENROUTER_BASE_URL), "OPENROUTER_BASE_URL is required for AI_PROVIDER=openrouter")' in text
    assert "get_task_model_config(task_name)" in text
    assert "OPENROUTER_API_KEY_CONFIGURED=" in text
    assert "OPENROUTER_REQUIRE_FREE_MODELS=" in text
    assert "PRIMARY_MODEL=" in text
    assert "FALLBACK_MODEL=" in text
    assert "Authorization" not in text


def test_runner_allows_configurable_database_and_redis_ports() -> None:
    text = _runner_text()

    assert "DATABASE_PORT must be 55432" not in text
    assert "REDIS_PORT must be 16379" not in text
    assert 'require_positive_int(db_port, "DATABASE_PORT must be a positive integer")' in text
    assert 'require_positive_int(redis_port, "REDIS_PORT must be a positive integer")' in text
