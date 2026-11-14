import os
from pathlib import Path
from typing import List

# Locate and load the nearest .env file (workspace root)
BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = BASE_DIR / ".env"

try:
    from dotenv import load_dotenv
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
    else:
        load_dotenv()
except ImportError:
    # Graceful manual parser if python-dotenv isn't installed yet
    if dotenv_path.exists():
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v


class Config:
    # Telegram settings
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    
    # Allowed numeric Telegram user ID (or comma-separated IDs)
    _raw_allowed = os.getenv("ALLOWED_USER_ID", "").strip()
    ALLOWED_USER_IDS: List[int] = []
    if _raw_allowed:
        for uid in _raw_allowed.split(","):
            uid = uid.strip()
            if uid.isdigit():
                ALLOWED_USER_IDS.append(int(uid))

    # LLM configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
    
    # Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-pro").strip()

    # Claude
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "").strip()
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5").strip()

    # Workspace directory
    _workspace = os.getenv("WORKSPACE_DIR", "").strip()
    WORKSPACE_DIR: Path = Path(_workspace).resolve() if _workspace else BASE_DIR

    # Indian Market defaults
    DEFAULT_CITY: str = os.getenv("DEFAULT_CITY", "Bengaluru, Karnataka, India").strip()
    _raw_cities = os.getenv("ACCEPTABLE_CITIES", "Bengaluru,Hyderabad,Mumbai,Pune,Ahmedabad,Gandhinagar,Remote")
    ACCEPTABLE_CITIES: List[str] = [c.strip() for c in _raw_cities.split(",") if c.strip()]

    @classmethod
    def validate(cls, require_telegram: bool = True) -> List[str]:
        """
        Validate configuration settings.
        Returns a list of warning or error messages (empty if all good).
        """
        errors = []
        if require_telegram:
            if not cls.TELEGRAM_BOT_TOKEN or cls.TELEGRAM_BOT_TOKEN == "your_bot_token_here":
                errors.append("TELEGRAM_BOT_TOKEN is missing or set to placeholder in .env")
            if not cls.ALLOWED_USER_IDS:
                errors.append("ALLOWED_USER_ID is not configured. Set your Telegram user ID in .env for security.")

        if cls.LLM_PROVIDER == "gemini":
            if not cls.GEMINI_API_KEY or cls.GEMINI_API_KEY == "your_gemini_api_key_here":
                errors.append("GEMINI_API_KEY is missing in .env (required because LLM_PROVIDER=gemini)")
        elif cls.LLM_PROVIDER == "claude":
            if not cls.ANTHROPIC_API_KEY:
                errors.append("ANTHROPIC_API_KEY is missing in .env (required because LLM_PROVIDER=claude)")
        else:
            errors.append(f"Invalid LLM_PROVIDER '{cls.LLM_PROVIDER}'. Must be 'gemini' or 'claude'.")

        if not cls.WORKSPACE_DIR.exists():
            errors.append(f"WORKSPACE_DIR does not exist: {cls.WORKSPACE_DIR}")

        return errors
