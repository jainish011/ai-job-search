from typing import Optional
from bot.config import Config
from bot.llm.base import LLMProvider
from bot.llm.gemini import GeminiProvider
from bot.llm.claude import ClaudeProvider

def get_llm_provider(
    provider_override: Optional[str] = None,
    model_override: Optional[str] = None
) -> LLMProvider:
    """
    Factory function returning an LLM provider based on Config or runtime override.
    """
    provider = (provider_override or Config.LLM_PROVIDER).strip().lower()

    if provider == "gemini":
        if not Config.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not set in your .env file. "
                "Add GEMINI_API_KEY=your_key to .env or switch provider via /llm claude."
            )
        model = model_override or Config.GEMINI_MODEL
        return GeminiProvider(api_key=Config.GEMINI_API_KEY, model_name=model)

    elif provider == "claude":
        if not Config.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set in your .env file. "
                "Add ANTHROPIC_API_KEY=your_key to .env or switch provider via /llm gemini."
            )
        model = model_override or Config.CLAUDE_MODEL
        return ClaudeProvider(api_key=Config.ANTHROPIC_API_KEY, model_name=model)

    else:
        raise ValueError(f"Unsupported LLM provider: '{provider}'. Supported: 'gemini', 'claude'")
