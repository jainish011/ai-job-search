---
framework_version: 1.0.0
---

# Agent Guidelines: AI Job Search

This workspace is structured to manage job search activities, scraper tools, CVs, cover letters, and interview preparation.

## Thin-Pointer Design (Single Source of Truth)

To prevent duplication and configuration drift across different AI agent frameworks (Claude Code, Google Antigravity, Codex, Cursor, Gemini CLI, etc.), this workspace uses a unified thin-pointer design. All agent runtimes should load the canonical specifications and candidate profiles from the files and directories below:

1. **Personal Candidate Profile:**
   - The candidate profile, contact details, education, and target preferences are defined in [CLAUDE.md](CLAUDE.md) and the individual profile methodology files under [.claude/skills/job-application-assistant/](.claude/skills/job-application-assistant/) (specifically `01-*.md` etc.).
2. **Canonical Workflow Specifications:**
   - The step-by-step instructions and triggers for tasks (setup, scrape, rank, apply, upskill, interview) are defined in the [.claude/](.claude/) directory (specifically under `.claude/skills/` and `.claude/commands/`).
   - Do not duplicate these rules or specifications. Treat `.claude/` files as the single source of truth.
3. **Portal Search Skills & Company Watchlist:**
   - Job-portal search CLIs live under [.agents/skills/](.agents/skills/) in the portable Agent Skills format.
   - Includes pure-Python LinkedIn search engine and `company-careers-watch` for direct ATS tracking.
4. **Telegram Mobile Bot & Multi-LLM Runtime:**
   - The workspace can be operated from any mobile device via the Telegram Bot in `bot/main.py`.
   - Supports Gemini Pro (`GEMINI_API_KEY`) and Claude (`ANTHROPIC_API_KEY`).
   - Setup guide available in [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md).
