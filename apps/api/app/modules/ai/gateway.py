import json
from typing import Any

from app.modules.ai.providers import Provider, build_provider
from app.modules.ai.schemas import GatewayResult


class ModelGateway:
    def __init__(self, provider: Provider | None = None) -> None:
        self.provider = provider or build_provider()

    def generate(
        self,
        task_name: str,
        prompt: str,
        response_schema: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GatewayResult:
        # Current AI tasks rely on task-configured JSON-object mode and the
        # existing parser validation; response_schema is preserved for callers
        # and passed through for providers that can use it later.
        return self.provider.generate_text(
            task_name=task_name,
            prompt=prompt,
            response_schema=response_schema,
            metadata=metadata,
        )

    def run(self, task_name: str, payload: dict[str, Any]) -> GatewayResult:
        prompt = json.dumps(payload, sort_keys=True, default=str)
        return self.provider.generate_text(
            task_name=task_name,
            prompt=prompt,
            response_schema=None,
            metadata=payload,
        )
