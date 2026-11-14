import os
import sys
import asyncio
from pathlib import Path

# Add project root to sys.path so 'bot' package resolves cleanly when run directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from bot.config import Config
from bot.llm.factory import get_llm_provider

async def test_llm():
    print(f"Configured provider: {Config.LLM_PROVIDER}")
    print(f"Using model: {Config.GEMINI_MODEL if Config.LLM_PROVIDER == 'gemini' else Config.CLAUDE_MODEL}")

    try:
        provider = get_llm_provider()
    except ValueError as e:
        print(f"\n[!] Provider setup check: {e}")
        print("    -> Open your .env file and set your API key to test live completions.")
        return

    print("\nSending quick test query to LLM...")
    try:
        response = await provider.complete(
            system_prompt="You are a helpful assistant. Reply concisely in one sentence.",
            user_message="Say hello and confirm you are ready to assist with job search in India."
        )
        print("\nResponse from LLM:")
        print(f"'{response.strip()}'")
        print("\n[OK] LLM connection verified successfully!")
    except Exception as e:
        print(f"\n[!] API call failed: {e}")
        print("    Please check that your API key is valid and has sufficient quota.")

if __name__ == "__main__":
    asyncio.run(test_llm())
