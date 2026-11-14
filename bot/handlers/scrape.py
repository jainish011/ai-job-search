import math
from typing import List, Dict, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.config import Config
from bot.utils.security import restricted
from bot.workflows.scrape_workflow import ScrapeWorkflow

PAGE_SIZE = 5
SEEN_JOBS_FILE = Config.WORKSPACE_DIR / "job_scraper" / "seen_jobs.json"

def save_jobs_to_history(jobs: List[Dict[str, Any]]) -> None:
    """Save scraped jobs to job_scraper/seen_jobs.json so /rank can find them."""
    import json
    import datetime
    SEEN_JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {"seen": {}}
    if SEEN_JOBS_FILE.exists():
        try:
            with open(SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {"seen": {}}

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    for j in jobs:
        url = j.get("url", "")
        company = j.get("company", "Company")
        title = j.get("title", "Role")
        key = f"{company}_{title}".lower().replace(" ", "_")
        data.setdefault("seen", {})[key] = {
            "title": title,
            "company": company,
            "url": url,
            "location": j.get("location"),
            "date": j.get("date"),
            "portal": j.get("portal", "ATS"),
            "first_seen": now_str
        }

    try:
        with open(SEEN_JOBS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[WARN] Failed writing to seen_jobs.json: {e}")

def build_page_content(
    jobs: List[Dict[str, Any]],
    query: str,
    page: int,
    total_pages: int
) -> tuple[str, InlineKeyboardMarkup]:
    start_idx = page * PAGE_SIZE
    end_idx = min(start_idx + PAGE_SIZE, len(jobs))
    page_jobs = jobs[start_idx:end_idx]

    lines = [
        f"🎯 *Active Postings matching '{query}' (Last 24 Hours)*",
        f"Showing {start_idx + 1}–{end_idx} of {len(jobs)} jobs (Page {page + 1}/{total_pages})\n"
    ]

    for i, j in enumerate(page_jobs, start_idx + 1):
        title = j.get("title", "Untitled Role")
        company = j.get("company", "Company")
        loc = j.get("location", "India")
        url = j.get("url", "")
        date = j.get("date", "Today")
        portal = j.get("portal", "ATS")

        lines.append(
            f"*{i}. {title}*\n"
            f"🏢 {company}  📍 {loc}\n"
            f"📅 Posted: `{date}`  via `{portal}`\n"
            f"🔗 [View Job Posting]({url})\n"
            f"👉 Apply: `/apply {url}`\n"
        )

    # Inline pagination keyboard
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"scrape_page:{page - 1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"scrape_page:{page + 1}"))

    keyboard = [nav_buttons] if nav_buttons else []
    markup = InlineKeyboardMarkup(keyboard)

    return "\n".join(lines), markup

@restricted
async def scrape_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for /scrape [query] [city]
    Discovers live jobs strictly posted in the last 24 hours, sorted newest first, with pagination.
    """
    if not update.effective_message:
        return

    args = context.args or []
    raw_args = " ".join(args).strip() if args else ""
    query = None
    location = None

    indian_cities = {c.lower() for c in Config.ACCEPTABLE_CITIES} | {"chennai", "kolkata", "india"}

    if raw_args:
        tokens = raw_args.split()
        if len(tokens) >= 2 and tokens[-1].lower() in indian_cities:
            location = tokens[-1].title()
            query = " ".join(tokens[:-1]).strip()
        elif len(tokens) == 1 and tokens[0].lower() in indian_cities:
            location = tokens[0].title()
            query = None
        else:
            query = raw_args

    search_label = query if query else "Backend & Software Engineer"
    status_msg = await update.effective_message.reply_text(
        f"⏱️ *Searching jobs posted in the LAST 24 HOURS...*\n"
        f"• Roles: `{search_label}`\n"
        f"• Locations: {location or ', '.join(Config.ACCEPTABLE_CITIES[:5])}...\n"
        f"• Sources: LinkedIn (Guest API) + Company Careers Watchlist\n\n"
        "Sorting newest first, please wait a moment...",
        parse_mode="Markdown"
    )

    try:
        workflow = ScrapeWorkflow()
        jobs = await workflow.run(
            query=query,
            location=location,
            limit_per_city=6,
            jobage_days=1  # strictly 24 hours
        )

        if not jobs:
            await status_msg.edit_text(
                f"⚠️ No active jobs posted in the *last 24 hours* matching `{query}` in your target locations.\n"
                "Try running again later or broaden your keywords (e.g. `/scrape Software Engineer`).",
                parse_mode="Markdown"
            )
            return

        # Store in user_data for pagination callback
        total_pages = math.ceil(len(jobs) / PAGE_SIZE)
        context.user_data["scrape_results"] = {
            "jobs": jobs,
            "query": search_label,
            "total_pages": total_pages
        }

        # Persist jobs to job_scraper/seen_jobs.json so /rank can find them across sessions
        save_jobs_to_history(jobs)

        text, markup = build_page_content(jobs, search_label, page=0, total_pages=total_pages)

        await status_msg.edit_text(
            text,
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=markup
        )

    except Exception as e:
        await status_msg.edit_text(
            f"❌ Search failed: `{str(e)}`\nPlease try again shortly.",
            parse_mode="Markdown"
        )

@restricted
async def scrape_pagination_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles inline Prev / Next button taps for /scrape results.
    """
    query = update.callback_query
    if not query:
        return

    await query.answer()

    data = query.data
    if not data or not data.startswith("scrape_page:"):
        return

    page = int(data.split(":")[1])
    scrape_data = context.user_data.get("scrape_results")
    if not scrape_data:
        await query.edit_message_text("⚠️ This search session expired. Run `/scrape` again.")
        return

    jobs = scrape_data["jobs"]
    search_query = scrape_data["query"]
    total_pages = scrape_data["total_pages"]

    text, markup = build_page_content(jobs, search_query, page, total_pages)

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        disable_web_page_preview=True,
        reply_markup=markup
    )
