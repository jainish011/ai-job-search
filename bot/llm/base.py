from abc import ABC, abstractmethod
from typing import Optional, AsyncIterator, Dict, Any

class LLMProvider(ABC):
    """
    Abstract interface for LLM providers (Gemini, Claude, etc.).
    Keeps the bot decoupled from any specific model or API vendor.
    """

    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> str:
        """
        Send a completion request to the LLM and return the text response.
        """
        pass

    @abstractmethod
    async def complete_stream(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs: Any
    ) -> AsyncIterator[str]:
        """
        Stream the completion response token-by-token (useful for live status or chunking).
        """
        pass
