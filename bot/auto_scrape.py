import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Ensure workspace root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from telegram import Bot
from bot.config import Config
from bot.workflows.scrape_workflow import ScrapeWorkflow
from bot.utils.message_splitter import split_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("auto_scrape")

HISTORY_FILE = Config.WORKSPACE_DIR / "job_scraper" / "seen_jobs.json"

def get_seen_urls() -> set:
    if not HISTORY_FILE.exists():
        return set()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            seen_dict = data.get("seen", {})
            return {v.get("url") for v in seen_dict.values() if isinstance(v, dict) and v.get("url")}
    except Exception as e:
        logger.warning(f"Failed to read seen jobs file: {e}")
        return set()

def record_seen_job(job: dict) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {"seen": {}}
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {"seen": {}}

    url = job.get("url", "")
    key = f"{job.get('company', '')}_{job.get('title', '')}".lower().replace(" ", "_")
    data.setdefault("seen", {})[key] = {
        "title": job.get("title"),
        "company": job.get("company"),
        "url": url,
        "location": job.get("location"),
        "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to update seen jobs: {e}")

async def run_auto_scrape() -> None:
    logger.info("Starting automated job search cycle...")
    
    if not Config.TELEGRAM_BOT_TOKEN or not Config.ALLOWED_USER_IDS:
        logger.error("TELEGRAM_BOT_TOKEN or ALLOWED_USER_ID is missing in .env. Cannot send notification.")
        return

    bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
    recipient_id = Config.ALLOWED_USER_IDS[0]

    workflow = ScrapeWorkflow()
    raw_results = await workflow.run(query="Backend Engineer", limit_per_city=5)

    seen = get_seen_urls()
    new_jobs = []

    for job in raw_results:
        u = job.get("url")
        if u and u not in seen:
            new_jobs.append(job)
            record_seen_job(job)

    if not new_jobs:
        logger.info("Auto-scrape completed: No new jobs detected since last run.")
        return

    logger.info(f"Discovered {len(new_jobs)} brand-new postings! Sending to Telegram...")

    lines = [
        f"🔔 *Automated Job Alert — {datetime.now().strftime('%d %b %Y, %I:%M %p')}*\n",
        f"Found *{len(new_jobs)} new roles* matching your profile:\n"
    ]

    for i, j in enumerate(new_jobs[:8], 1):
        title = j.get("title", "Role")
        company = j.get("company", "Company")
        loc = j.get("location", "India")
        url = j.get("url", "")
        lines.append(
            f"*{i}. {title}* at {company}\n"
            f"📍 {loc} • [View Posting]({url})\n"
            f"👉 `/apply {url}`\n"
        )

    full_text = "\n".join(lines)
    chunks = split_message(full_text)

    for chunk in chunks:
        await bot.send_message(
            chat_id=recipient_id,
            text=chunk,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

    logger.info("Notification sent successfully.")

if __name__ == "__main__":
    asyncio.run(run_auto_scrape())
