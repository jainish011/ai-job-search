from functools import wraps
from typing import Callable, Any
from telegram import Update
from telegram.ext import ContextTypes
from bot.config import Config

def restricted(func: Callable) -> Callable:
    """
    Decorator for Telegram command handlers to verify that the incoming user
    matches Config.ALLOWED_USER_IDS.
    If no ALLOWED_USER_IDS is configured, allows and prints a prominent console warning.
    """
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args: Any, **kwargs: Any) -> Any:
        user = update.effective_user
        if not user:
            return None

        allowed_ids = Config.ALLOWED_USER_IDS

        if not allowed_ids:
            # If user hasn't set ALLOWED_USER_ID in .env yet, warn but permit in local dev
            print(f"[SECURITY WARNING] ALLOWED_USER_ID not configured in .env. Request from user id: {user.id} ({user.username})")
            return await func(update, context, *args, **kwargs)

        if user.id not in allowed_ids:
            print(f"[UNAUTHORIZED] Blocked attempt from user ID: {user.id} (@{user.username or 'unknown'})")
            if update.effective_message:
                await update.effective_message.reply_text(
                    "⛔ *Unauthorized*\nThis is a private AI Job Search assistant bot. "
                    "Access is restricted to the owner.",
                    parse_mode="Markdown"
                )
            return None

        return await func(update, context, *args, **kwargs)

    return wrapped
