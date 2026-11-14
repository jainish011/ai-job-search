import os
from pathlib import Path
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes

async def send_pdf_document(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    file_path: Path,
    caption: Optional[str] = None
) -> bool:
    """
    Send a compiled PDF document (e.g. CV or Cover Letter) to the user's Telegram chat.
    Returns True if sent successfully, False otherwise.
    """
    if not update.effective_chat:
        return False

    resolved_path = Path(file_path).resolve()
    if not resolved_path.exists() or not resolved_path.is_file():
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"⚠️ File not found: `{resolved_path.name}`",
            parse_mode="Markdown"
        )
        return False

    try:
        with open(resolved_path, "rb") as doc:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=doc,
                filename=resolved_path.name,
                caption=caption
            )
        return True
    except Exception as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"❌ Failed to send document `{resolved_path.name}`: {str(e)}",
            parse_mode="Markdown"
        )
        return False
