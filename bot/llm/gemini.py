import asyncio
from typing import Optional, AsyncIterator, Any
from bot.llm.base import LLMProvider

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-pro"):
        self.api_key = api_key
        self.model_name = model_name
        self._configured = False

    def _ensure_configured(self):
        if not self._configured:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._configured = True

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        self._ensure_configured()
        import google.generativeai as genai

        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens
        )

        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt if system_prompt else None,
            generation_config=generation_config
        )

        # Run synchronously in executor to keep interface async
        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content(user_message)
        )

        if not response or not response.text:
            return ""
        return response.text

    async def complete_stream(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> AsyncIterator[str]:
        self._ensure_configured()
        import google.generativeai as genai

        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens
        )

        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt if system_prompt else None,
            generation_config=generation_config
        )

        loop = asyncio.get_running_loop()
        response_stream = await loop.run_in_executor(
            None,
            lambda: model.generate_content(user_message, stream=True)
        )

        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
