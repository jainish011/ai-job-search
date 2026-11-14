import sys
import logging
from pathlib import Path
from telegram import BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes

# Ensure workspace root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from bot.config import Config
from bot.handlers.general import (
    start_command,
    help_command,
    status_command,
    llm_command
)
from bot.handlers.scrape import scrape_command, scrape_pagination_callback
from bot.handlers.apply import apply_command
from bot.handlers.rank import rank_command
from bot.handlers.interview import interview_command
from bot.handlers.report import report_command
from bot.handlers.setup import setup_command, handle_document_or_text_message
from bot.handlers.watchlist import watchlist_command
from telegram.ext import MessageHandler, CallbackQueryHandler, filters

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("ai_job_search_bot")

async def post_init(application: Application) -> None:
    """Set up Telegram bot commands menu in the chat UI."""
    commands = [
        BotCommand("start", "Start assistant & introduction"),
        BotCommand("setup", "Import resume PDF or text into profile"),
        BotCommand("scrape", "Search for new job openings"),
        BotCommand("watchlist", "Manage target company ATS watchlist"),
        BotCommand("apply", "Evaluate fit & tailor application"),
        BotCommand("rank", "Batch score scraped jobs"),
        BotCommand("interview", "Prepare for interviews"),
        BotCommand("report", "View application pipeline report"),
        BotCommand("status", "Show bot & LLM settings"),
        BotCommand("llm", "Switch active LLM (gemini/claude)"),
        BotCommand("help", "List all available commands")
    ]
    try:
        await application.bot.set_my_commands(commands)
        logger.info("Bot commands menu registered successfully.")
    except Exception as e:
        logger.warning(f"Failed to register commands menu: {e}")

def create_application() -> Application:
    validation_errors = Config.validate(require_telegram=True)
    if validation_errors:
        for err in validation_errors:
            logger.error(f"[CONFIG ERROR] {err}")
        print("\n" + "="*60)
        print("❌ Cannot start bot due to configuration issues.")
        print("Please check your .env file. Required values:")
        print("  - TELEGRAM_BOT_TOKEN")
        print("  - ALLOWED_USER_ID")
        print("  - GEMINI_API_KEY (or ANTHROPIC_API_KEY)")
        print("="*60 + "\n")
        sys.exit(1)

    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # Core general command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("setup", setup_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("llm", llm_command))
    app.add_handler(CommandHandler("watchlist", watchlist_command))
    app.add_handler(CommandHandler("scrape", scrape_command))
    app.add_handler(CommandHandler("apply", apply_command))
    app.add_handler(CommandHandler("rank", rank_command))
    app.add_handler(CommandHandler("interview", interview_command))
    app.add_handler(CommandHandler("report", report_command))

    # Pagination callback for /scrape results
    app.add_handler(CallbackQueryHandler(scrape_pagination_callback, pattern=r"^scrape_page:\d+$"))

    # Catch documents (resume PDF) and text messages for onboarding / interactive flows
    app.add_handler(MessageHandler(filters.Document.ALL | filters.TEXT & ~filters.COMMAND, handle_document_or_text_message))

    return app

def main() -> None:
    logger.info("Starting AI Job Search Telegram Bot (Long-polling)...")
    app = create_application()
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
