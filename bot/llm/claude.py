import asyncio
from typing import Optional, AsyncIterator, Any
from bot.llm.base import LLMProvider

class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str = "claude-sonnet-4-5"):
        self.api_key = api_key
        self.model_name = model_name
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        self._ensure_client()
        tokens = max_tokens or 4096

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self._client.messages.create(
                model=self.model_name,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                temperature=temperature,
                max_tokens=tokens
            )
        )

        return "".join([block.text for block in response.content if hasattr(block, "text")])

    async def complete_stream(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> AsyncIterator[str]:
        self._ensure_client()
        tokens = max_tokens or 4096

        with self._client.messages.stream(
            model=self.model_name,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            temperature=temperature,
            max_tokens=tokens
        ) as stream:
            for text in stream.text_stream:
                yield text
