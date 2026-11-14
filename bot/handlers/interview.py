from telegram import Update
from telegram.ext import ContextTypes

from bot.utils.security import restricted
from bot.utils.message_splitter import split_message
from bot.workflows.base_workflow import BaseWorkflow

@restricted
async def interview_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for /interview [company or role]
    Generates interview prep pack with STAR responses and high-impact questions.
    """
    if not update.effective_message:
        return

    args = context.args or []
    target = " ".join(args) if args else "Target Technical Role"

    status_msg = await update.effective_message.reply_text(
        f"🎯 *Preparing Interview Strategy for: {target}...*\n"
        "Synthesizing your experience into STAR-format talking points...",
        parse_mode="Markdown"
    )

    try:
        workflow = BaseWorkflow()
        profile_context = workflow.get_candidate_profile_context()
        interview_rules = workflow.read_file(".claude/skills/job-application-assistant/07-interview-prep.md")

        system_prompt = (
            "You are an executive tech interview coach preparing a candidate for a technical interview in India.\n"
            f"{profile_context}\n\n"
            f"=== COACHING METHODOLOGY ===\n{interview_rules}\n\n"
            "Generate a high-impact interview preparation pack including:\n"
            "1. **Elevator Pitch (30-sec Self Introduction)**\n"
            "2. **Top 3 Likely Technical & Architecture Questions** with tailored answer outlines\n"
            "3. **2 STAR Behavioral Examples** from the candidate's actual background\n"
            "4. **Smart Reverse-Interview Questions** to ask the hiring team/engineering manager"
        )

        prompt = f"Please generate a complete interview prep pack for: {target}"

        response = await workflow.llm.complete(
            system_prompt=system_prompt,
            user_message=prompt,
            temperature=0.3
        )

        chunks = split_message(f"🎙️ *Interview Prep Pack — {target}*\n\n{response}")
        await status_msg.edit_text(chunks[0], parse_mode="Markdown")

        for chunk in chunks[1:]:
            await update.effective_message.reply_text(chunk, parse_mode="Markdown")

    except Exception as e:
        await status_msg.edit_text(
            f"❌ Interview prep generation failed: `{str(e)}`",
            parse_mode="Markdown"
        )
