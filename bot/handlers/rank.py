import json
from pathlib import Path
from typing import List, Dict, Any
from telegram import Update
from telegram.ext import ContextTypes

from bot.config import Config
from bot.utils.security import restricted
from bot.utils.message_splitter import split_message, send_safe_markdown
from bot.workflows.base_workflow import BaseWorkflow
from bot.workflows.apply_workflow import ApplyWorkflow

SEEN_JOBS_FILE = Config.WORKSPACE_DIR / "job_scraper" / "seen_jobs.json"

@restricted
async def rank_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler for /rank [<url> | <focus area>]
    Can score a specific job URL directly, or batch-rank the recently scraped jobs.
    """
    if not update.effective_message:
        return

    args = context.args or []
    target_input = " ".join(args).strip() if args else ""

    workflow = BaseWorkflow()
    profile_context = workflow.get_candidate_profile_context()

    # Case 1: User passed a specific URL directly to /rank <url>
    if target_input.startswith("http://") or target_input.startswith("https://"):
        status_msg = await update.effective_message.reply_text(
            f"📊 *Scoring & Ranking target posting...*\n`{target_input}`",
            parse_mode="Markdown"
        )
        try:
            apply_wf = ApplyWorkflow()
            job_text = await apply_wf.fetch_job_text_if_url(target_input)

            system_prompt = (
                "You are an expert career strategist evaluating a job posting for a candidate in India.\n"
                f"{profile_context}\n\n"
                "Evaluate and return a structured Fit Ranking in clean Markdown:\n"
                "1. **Overall Fit Score: X/100** (e.g. 85/100 - Strong Fit / Moderate Fit / Weak Fit)\n"
                "2. **Top Strengths Match** (2-3 bullet points)\n"
                "3. **Skill / Experience Gaps** (1-2 honest bridge notes)\n"
                "4. **Location & Commute Alignment**\n"
                "5. **Action Recommendation**\n"
                "👉 To tailor application: `/apply <url>`"
            )

            prompt = f"Target Posting URL: {target_input}\n\nJob Content:\n{job_text[:6000]}"
            response = await workflow.llm.complete(system_prompt=system_prompt, user_message=prompt)

            await send_safe_markdown(
                bot=context.bot,
                chat_id=update.effective_chat.id,
                text=f"🏆 *Fit Rank Assessment:*\n\n{response}",
                edit_message_id=status_msg.message_id
            )
            return

        except Exception as e:
            await status_msg.edit_text(f"❌ Ranking failed: `{str(e)}`", parse_mode="Markdown")
            return

    # Case 2: Batch-ranking jobs from recent scrape session or seen_jobs.json
    status_msg = await update.effective_message.reply_text(
        "📊 *Evaluating & Ranking Jobs...*\n"
        "Loading recent postings and scoring alignment against your background...",
        parse_mode="Markdown"
    )

    try:
        # Check active session memory from /scrape first
        scrape_session = context.user_data.get("scrape_results", {})
        jobs_to_rank = scrape_session.get("jobs", [])

        # If not in session memory, read from seen_jobs.json
        if not jobs_to_rank and SEEN_JOBS_FILE.exists():
            with open(SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                seen_dict = data.get("seen", {})
                jobs_to_rank = list(seen_dict.values())[-12:]

        if not jobs_to_rank:
            await status_msg.edit_text(
                "ℹ️ No scraped jobs found to rank yet.\n"
                "Run `/scrape` first to discover active postings, or rank a specific job using:\n"
                "`/rank <job_url>`",
                parse_mode="Markdown"
            )
            return

        # If user passed a keyword focus (e.g. /rank python)
        if target_input:
            jobs_to_rank = [
                j for j in jobs_to_rank
                if target_input.lower() in (j.get("title", "") + " " + j.get("company", "")).lower()
            ] or jobs_to_rank[:10]

        jobs_summary = "\n".join([
            f"- Role: {j.get('title')} at {j.get('company')} ({j.get('location')}) | Link: {j.get('url')}"
            for j in jobs_to_rank[:10]
        ])

        system_prompt = (
            "You are an expert technical career strategist in India evaluating jobs for Jainish Chauhan.\n"
            f"{profile_context}\n\n"
            "Evaluation Rules:\n"
            "- Accurately calculate the candidate's exact cumulative experience dynamically using the Current Date provided in the context.\n"
            "- Return a clean, scannable Markdown list.\n"
            "- Do NOT use unclosed markdown entities like single underscores or unmatched backticks.\n"
            "- For each role, provide:\n"
            "  • Numbered Rank: Role at Company (Location) — Score/100 (Fit Level)\n"
            "  • Rationale: 1-2 concise bullet points highlighting match & experience level alignment\n"
            "  • Action: /apply <url>"
        )

        response = await workflow.llm.complete(
            system_prompt=system_prompt,
            user_message=f"Please rank these postings:\n\n{jobs_summary}",
            temperature=0.2
        )

        await send_safe_markdown(
            bot=context.bot,
            chat_id=update.effective_chat.id,
            text=f"🏆 *Ranked Shortlist ({len(jobs_to_rank[:10])} jobs evaluated):*\n\n{response}",
            edit_message_id=status_msg.message_id
        )

    except Exception as e:
        await status_msg.edit_text(
            f"❌ Ranking failed: `{str(e)}`",
            parse_mode="Markdown"
        )
