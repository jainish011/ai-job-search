import json
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes

from bot.config import Config
from bot.utils.security import restricted

WATCHLIST_FILE = Config.WORKSPACE_DIR / ".agents" / "skills" / "company-careers-watch" / "watchlist.json"

@restricted
async def watchlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for /watchlist [add <name> <ats> <slug> [careers_url] | list | remove <name>]
    Manage companies on your ATS careers watchlist.
    """
    if not update.effective_message:
        return

    args = context.args or []
    WATCHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Load existing watchlist
    watchlist_data = {"companies": []}
    if WATCHLIST_FILE.exists():
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                watchlist_data = json.load(f)
        except Exception:
            watchlist_data = {"companies": []}

    companies = watchlist_data.get("companies", [])

    if not args or args[0].lower() == "list":
        if not companies:
            await update.effective_message.reply_text(
                "📋 *Your Company Careers Watchlist is Empty.*\n\n"
                "Add companies using:\n"
                "`/watchlist add <Company> <greenhouse|lever> <slug>`\n\n"
                "Example:\n"
                "`/watchlist add Razorpay greenhouse razorpay`",
                parse_mode="Markdown"
            )
            return

        lines = [f"📋 *Target Companies Watchlist ({len(companies)} tracked):*\n"]
        for i, c in enumerate(companies, 1):
            name = c.get("name", "Unknown")
            ats = c.get("ats", "unknown")
            slug = c.get("slug", "")
            lines.append(f"*{i}. {name}* (`{ats}`: `{slug}`)")

        lines.append("\n💡 *Commands:*")
        lines.append("• Add: `/watchlist add <name> <greenhouse|lever> <slug>`")
        lines.append("• Remove: `/watchlist remove <name>`")

        await update.effective_message.reply_text("\n".join(lines), parse_mode="Markdown")
        return

    subcmd = args[0].lower()

    if subcmd == "add":
        if len(args) < 4:
            await update.effective_message.reply_text(
                "⚠️ *Usage:*\n`/watchlist add <Company Name> <greenhouse|lever> <slug> [careers_url]`\n\n"
                "Example:\n`/watchlist add Zepto greenhouse zepto`\n"
                "`/watchlist add Swiggy lever swiggy`",
                parse_mode="Markdown"
            )
            return

        company_name = args[1].strip()
        ats_type = args[2].strip().lower()
        slug = args[3].strip()
        careers_url = args[4].strip() if len(args) > 4 else f"https://{slug}.com/careers"

        if ats_type not in ("greenhouse", "lever", "ashby", "workday"):
            await update.effective_message.reply_text("⚠️ ATS type must be `greenhouse` or `lever`.")
            return

        # Check if already exists
        existing = next((c for c in companies if c.get("name", "").lower() == company_name.lower()), None)
        if existing:
            existing["ats"] = ats_type
            existing["slug"] = slug
            existing["careers_url"] = careers_url
            msg = f"🔄 Updated *{company_name}* on your watchlist."
        else:
            companies.append({
                "name": company_name,
                "ats": ats_type,
                "slug": slug,
                "careers_url": careers_url
            })
            msg = f"✅ Added *{company_name}* to your company careers watchlist."

        watchlist_data["companies"] = companies
        with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
            json.dump(watchlist_data, f, indent=2)

        await update.effective_message.reply_text(
            f"{msg}\nIt will now be automatically polled when you run `/scrape`.",
            parse_mode="Markdown"
        )

    elif subcmd == "remove" or subcmd == "rm":
        if len(args) < 2:
            await update.effective_message.reply_text("⚠️ *Usage:* `/watchlist remove <Company Name>`", parse_mode="Markdown")
            return

        target_name = " ".join(args[1:]).strip().lower()
        new_companies = [c for c in companies if c.get("name", "").lower() != target_name]

        if len(new_companies) == len(companies):
            await update.effective_message.reply_text(f"⚠️ Company `{target_name}` not found in watchlist.")
            return

        watchlist_data["companies"] = new_companies
        with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
            json.dump(watchlist_data, f, indent=2)

        await update.effective_message.reply_text(f"🗑️ Removed *{target_name.capitalize()}* from your watchlist.", parse_mode="Markdown")

    else:
        await update.effective_message.reply_text(
            "⚠️ Unknown action. Use:\n• `/watchlist list`\n• `/watchlist add <name> <ats> <slug>`\n• `/watchlist remove <name>`",
            parse_mode="Markdown"
        )
