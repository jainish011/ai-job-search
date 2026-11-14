import csv
from telegram import Update
from telegram.ext import ContextTypes

from bot.config import Config
from bot.utils.security import restricted
from bot.utils.message_splitter import split_message

TRACKER_FILE = Config.WORKSPACE_DIR / "job_search_tracker.csv"

@restricted
async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for /report
    Generates a live pipeline summary of all tracked job applications.
    """
    if not update.effective_message:
        return

    if not TRACKER_FILE.exists():
        await update.effective_message.reply_text(
            "📊 *Job Search Pipeline Summary*\n\n"
            "No applications tracked in `job_search_tracker.csv` yet.\n"
            "Once you run `/apply`, jobs will automatically be recorded here.",
            parse_mode="Markdown"
        )
        return

    try:
        rows = []
        with open(TRACKER_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)

        if not rows:
            await update.effective_message.reply_text(
                "📊 *Pipeline Empty*\nStart tailoring applications using `/apply`.",
                parse_mode="Markdown"
            )
            return

        status_counts = {}
        for r in rows:
            st = r.get("status", "drafted").lower()
            status_counts[st] = status_counts.get(st, 0) + 1

        summary_lines = [
            f"📊 *Job Application Pipeline Report ({len(rows)} Total)*\n",
            "📌 *Status Breakdown:*"
        ]
        for st, count in status_counts.items():
            summary_lines.append(f"• `{st.capitalize()}`: *{count}*")

        summary_lines.append("\n🕒 *Recent Applications:*")
        for r in rows[-5:]:
            comp = r.get("company", "Company")
            role = r.get("role", "Role")
            st = r.get("status", "drafted")
            date_val = r.get("date", "")
            summary_lines.append(f"• *{comp}* - {role} (`{st}`) {f'[{date_val}]' if date_val else ''}")

        full_text = "\n".join(summary_lines)
        chunks = split_message(full_text)

        for chunk in chunks:
            await update.effective_message.reply_text(chunk, parse_mode="Markdown")

    except Exception as e:
        await update.effective_message.reply_text(f"❌ Failed to generate report: {e}")
