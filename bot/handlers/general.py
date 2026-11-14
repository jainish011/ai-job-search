from telegram import Update
from telegram.ext import ContextTypes
from bot.config import Config
from bot.utils.security import restricted

@restricted
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    greeting = f"Hello {user.first_name}!" if user else "Hello!"
    text = (
        f"👋 *{greeting}*\n\n"
        "Welcome to your personal *AI Job Search Assistant*.\n"
        "This bot helps you search jobs, tailor CVs & cover letters, and track your pipeline.\n\n"
        "🎯 *Core Commands:*\n"
        "• `/scrape` - Search Indian & international job boards\n"
        "• `/apply <url or text>` - Evaluate job fit & tailor CV/cover letter\n"
        "• `/rank` - Score scraped jobs into a prioritized shortlist\n"
        "• `/interview` - Generate interview prep pack & talking points\n"
        "• `/status` - View current bot config, active LLM & locations\n"
        "• `/llm [gemini|claude]` - View or switch the active LLM provider\n\n"
        "Type `/help` to see the full list of available commands."
    )
    if update.effective_message:
        await update.effective_message.reply_text(text, parse_mode="Markdown")

@restricted
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📋 *AI Job Search Assistant — Command Reference*\n\n"
        "🔍 *Job Discovery & Company Watchlist:*\n"
        "• `/scrape [role] [city]` - Scrape active postings across Indian tech hubs\n"
        "• `/rank` - Batch-evaluate & rank scraped jobs with fit scores\n"
        "• `/watchlist list` - View target companies on your careers watchlist\n"
        "• `/watchlist add <company> <ats> <slug>` - Add company ATS to watch (e.g. Greenhouse/Lever)\n"
        "• `/watchlist remove <company>` - Remove company from watchlist\n\n"
        "📝 *Profile & Tailored Applications:*\n"
        "• `/setup` - Ingest your resume PDF or text into candidate profile\n"
        "• `/apply <url or text>` - Evaluate job fit & draft tailored CV/Cover Letter\n"
        "• `/report` - View job application pipeline & stats\n\n"
        "🎯 *Interview & Career Strategy:*\n"
        "• `/interview [role/company]` - Generate STAR interview prep pack & talking points\n"
        "• `/status` - Check active LLM, model, target cities, and health\n"
        "• `/llm [gemini|claude]` - Switch active LLM provider dynamically"
    )
    if update.effective_message:
        await update.effective_message.reply_text(text, parse_mode="Markdown")

@restricted
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    active_provider = context.user_data.get("llm_provider", Config.LLM_PROVIDER)
    active_model = Config.GEMINI_MODEL if active_provider == "gemini" else Config.CLAUDE_MODEL

    text = (
        "⚙️ *Bot Configuration & Status*\n\n"
        f"• *Active LLM Provider:* `{active_provider.upper()}`\n"
        f"• *Model:* `{active_model}`\n"
        f"• *Default City:* {Config.DEFAULT_CITY}\n"
        f"• *Allowed Cities:* {', '.join(Config.ACCEPTABLE_CITIES[:4])}...\n"
        f"• *Workspace:* `{Config.WORKSPACE_DIR.name}`\n"
        f"• *Allowed Users:* `{len(Config.ALLOWED_USER_IDS)} registered`\n"
    )
    if update.effective_message:
        await update.effective_message.reply_text(text, parse_mode="Markdown")

@restricted
async def llm_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    current = context.user_data.get("llm_provider", Config.LLM_PROVIDER)

    if not args:
        text = (
            f"🤖 *Active LLM Provider:* `{current.upper()}`\n\n"
            "To switch provider, run:\n"
            "• `/llm gemini` - Use Google Gemini (Pro/Flash)\n"
            "• `/llm claude` - Use Anthropic Claude"
        )
        if update.effective_message:
            await update.effective_message.reply_text(text, parse_mode="Markdown")
        return

    target = args[0].strip().lower()
    if target in ("gemini", "claude"):
        context.user_data["llm_provider"] = target
        if update.effective_message:
            await update.effective_message.reply_text(
                f"✅ Switched active LLM provider to *{target.upper()}*.",
                parse_mode="Markdown"
            )
    else:
        if update.effective_message:
            await update.effective_message.reply_text(
                "❌ Invalid provider. Choose either `/llm gemini` or `/llm claude`."
            )
