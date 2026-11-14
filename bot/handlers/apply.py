from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.config import Config
from bot.utils.security import restricted
from bot.utils.message_splitter import split_message, send_safe_markdown
from bot.utils.pdf_sender import send_pdf_document
from bot.workflows.apply_workflow import ApplyWorkflow

@restricted
async def apply_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for /apply <url or pasted text>
    Evaluates fit, generates tailored CV/Cover Letter, and sends PDFs.
    """
    if not update.effective_message:
        return

    args = context.args or []
    if not args and not (update.effective_message.reply_to_message and update.effective_message.reply_to_message.text):
        await update.effective_message.reply_text(
            "📝 *Usage:* `/apply <job url or pasted job description>`\n\n"
            "You can also reply to any message containing a job description with `/apply`.",
            parse_mode="Markdown"
        )
        return

    job_input = " ".join(args) if args else (update.effective_message.reply_to_message.text or "")

    status_msg = await update.effective_message.reply_text(
        "⚡ *Tailoring Resume for Role...*\n"
        "Aligning key technical achievements & skills to job requirements...",
        parse_mode="Markdown"
    )

    try:
        workflow = ApplyWorkflow()
        context.user_data["last_applied_job"] = job_input

        # Directly generate tailored resume (single pass, fast & token-efficient)
        cv_pdf, cover_pdf, notes = await workflow.draft_and_compile(job_input)

        if cv_pdf and cv_pdf.exists():
            await send_pdf_document(
                update,
                context,
                cv_pdf,
                caption="📄 *Tailored CV (Compiled PDF)*"
            )

        if cover_pdf and cover_pdf.exists():
            await send_pdf_document(
                update,
                context,
                cover_pdf,
                caption="✉️ *Tailored Cover Letter (Compiled PDF)*"
            )

        await status_msg.edit_text(
            f"✅ *Resume Tailoring Completed!*\n\n{notes}",
            parse_mode="Markdown"
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        await status_msg.edit_text(
            f"❌ Tailoring failed: `{str(e)}`\n"
            "Please verify your LLM API key in `.env`.",
            parse_mode="Markdown"
        )
