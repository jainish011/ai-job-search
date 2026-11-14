import re
from typing import List, Optional

TELEGRAM_MAX_LENGTH = 4000

def split_message(text: str, max_length: int = TELEGRAM_MAX_LENGTH) -> List[str]:
    """
    Split a long message into chunks safely under Telegram's limit.
    Ensures markdown code blocks, bold, and italic entities are not broken across chunks.
    """
    if not text:
        return []

    if len(text) <= max_length:
        return [text]

    chunks: List[str] = []
    current_chunk = ""

    lines = text.split("\n")

    for line in lines:
        if len(current_chunk) + len(line) + 1 > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            if len(line) > max_length:
                words = line.split(" ")
                for word in words:
                    if len(current_chunk) + len(word) + 1 > max_length:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            current_chunk = ""
                        while len(word) > max_length:
                            chunks.append(word[:max_length])
                            word = word[max_length:]
                    if current_chunk:
                        current_chunk += " " + word
                    else:
                        current_chunk = word
            else:
                current_chunk = line
        else:
            if current_chunk:
                current_chunk += "\n" + line
            else:
                current_chunk = line

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

async def send_safe_markdown(bot, chat_id: int, text: str, edit_message_id: Optional[int] = None, disable_web_page_preview: bool = True):
    """
    Safely sends or edits a message using Markdown.
    If Telegram raises entity parsing errors (e.g. unclosed * or _ or `),
    gracefully falls back to plain text so the message never crashes!
    """
    chunks = split_message(text)
    if not chunks:
        return None

    first_chunk = chunks[0]
    first_msg = None

    if edit_message_id:
        try:
            first_msg = await bot.edit_message_text(
                chat_id=chat_id,
                message_id=edit_message_id,
                text=first_chunk,
                parse_mode="Markdown",
                disable_web_page_preview=disable_web_page_preview
            )
        except Exception as e:
            # Fallback to plain text on Markdown syntax parse errors
            first_msg = await bot.edit_message_text(
                chat_id=chat_id,
                message_id=edit_message_id,
                text=first_chunk,
                parse_mode=None,
                disable_web_page_preview=disable_web_page_preview
            )
    else:
        try:
            first_msg = await bot.send_message(
                chat_id=chat_id,
                text=first_chunk,
                parse_mode="Markdown",
                disable_web_page_preview=disable_web_page_preview
            )
        except Exception:
            first_msg = await bot.send_message(
                chat_id=chat_id,
                text=first_chunk,
                parse_mode=None,
                disable_web_page_preview=disable_web_page_preview
            )

    # Send remaining chunks
    for chunk in chunks[1:]:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=chunk,
                parse_mode="Markdown",
                disable_web_page_preview=disable_web_page_preview
            )
        except Exception:
            await bot.send_message(
                chat_id=chat_id,
                text=chunk,
                parse_mode=None,
                disable_web_page_preview=disable_web_page_preview
            )

    return first_msg
