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
        return self.provider.generate_text(
            task_name=task_name,
            prompt=prompt,
            metadata=metadata,
        )
