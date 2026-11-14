import io
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
import pypdf

from bot.config import Config
from bot.utils.security import restricted
from bot.workflows.setup_workflow import SetupWorkflow

@restricted
async def setup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for /setup.
    Guides the user to import their resume (upload PDF or paste text)
    to automatically populate CLAUDE.md and profile skills.
    """
    if not update.effective_message:
        return

    args = context.args or []
    
    if args:
        # User supplied resume text directly via /setup <pasted text>
        resume_text = " ".join(args)
        await _process_resume_text(update, context, resume_text)
        return

    # Check if user replied to a message or attached a document
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.text:
        await _process_resume_text(update, context, msg.reply_to_message.text)
        return

    # Check if a document is attached directly with /setup caption
    if msg.document:
        await _process_resume_document(update, context, msg.document)
        return

    # Set state waiting for resume
    context.user_data["awaiting_resume_import"] = True

    await update.effective_message.reply_text(
        "📄 *Profile Setup & Resume Ingestion*\n\n"
        "To build your candidate profile, you can:\n"
        "1. **Send your resume PDF** as a document right here in chat.\n"
        "2. **Paste your resume text** directly in your next message.\n\n"
        "I will extract your experience, skills, projects, and education into `CLAUDE.md` "
        "so that `/apply` will automatically generate tailored CVs matching your actual background.",
        parse_mode="Markdown"
    )

async def _process_resume_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    context.user_data["awaiting_resume_import"] = False
    status_msg = await update.effective_message.reply_text(
        "🧠 *Parsing Resume & Extracting Profile Facts...*\n"
        "Extracting your skills, experience, and education...",
        parse_mode="Markdown"
    )

    try:
        workflow = SetupWorkflow()
        updated_profile = await workflow.ingest_resume(text)

        await status_msg.edit_text(
            "✅ *Profile Setup Complete!*\n\n"
            "Your profile has been extracted and saved to `CLAUDE.md` and `01-candidate-profile.md`.\n"
            "All future `/apply` commands will tailor CVs and cover letters directly from your background.\n\n"
            "Next steps:\n"
            "• `/scrape` - Find matching jobs\n"
            "• `/apply <job url or text>` - Tailor an application",
            parse_mode="Markdown"
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ Failed to parse resume: {e}")

async def _process_resume_document(update: Update, context: ContextTypes.DEFAULT_TYPE, document) -> None:
    context.user_data["awaiting_resume_import"] = False
    
    if not document.file_name.lower().endswith(".pdf"):
        await update.effective_message.reply_text("⚠️ Please send your resume as a **PDF** or paste the raw text.")
        return

    status_msg = await update.effective_message.reply_text(
        "📥 *Downloading & reading your resume PDF...*",
        parse_mode="Markdown"
    )

    try:
        tg_file = await document.get_file()
        file_bytes = io.BytesIO()
        await tg_file.download_to_memory(file_bytes)
        file_bytes.seek(0)

        reader = pypdf.PdfReader(file_bytes)
        extracted_text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                extracted_text += t + "\n"

        if not extracted_text.strip():
            await status_msg.edit_text("⚠️ Could not extract text from this PDF (it might be a scanned image). Please paste text directly.")
            return

        # Save copy into documents/cv/
        cv_dest = Config.WORKSPACE_DIR / "documents" / "cv" / document.file_name
        cv_dest.parent.mkdir(parents=True, exist_ok=True)
        with open(cv_dest, "wb") as f:
            f.write(file_bytes.getvalue())

        await status_msg.edit_text("🧠 *Parsing extracted resume text & updating candidate profile...*", parse_mode="Markdown")

        workflow = SetupWorkflow()
        await workflow.ingest_resume(extracted_text)

        await status_msg.edit_text(
            f"✅ *Resume PDF Ingested Successfully! (`{document.file_name}`)*\n\n"
            "Saved to `documents/cv/` and extracted your profile into `CLAUDE.md`.\n\n"
            "You are ready to search and apply:\n"
            "• `/scrape` - Search for jobs\n"
            "• `/apply <job url>` - Tailor CV and cover letter",
            parse_mode="Markdown"
        )

    except Exception as e:
        await status_msg.edit_text(f"❌ PDF ingestion error: {e}")

@restricted
async def handle_document_or_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Catch-all message handler for when user is in the middle of /setup flow.
    """
    if not update.effective_message:
        return

    if context.user_data.get("awaiting_resume_import"):
        if update.effective_message.document:
            await _process_resume_document(update, context, update.effective_message.document)
        elif update.effective_message.text:
            await _process_resume_text(update, context, update.effective_message.text)
