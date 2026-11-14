# AI Job Search — Telegram Bot Setup Guide (Windows)

This guide walks you through setting up and running your AI Job Search assistant on Telegram from your Windows machine.

---

## 1. Create Your Telegram Bot

1. Open Telegram and search for **[@BotFather](https://t.me/BotFather)**.
2. Send `/newbot` and follow the instructions:
   - Provide a name (e.g. `My AI Job Assistant`)
   - Provide a username ending in `bot` (e.g. `jainish_job_search_bot`)
3. Copy the **HTTP API Bot Token** provided by BotFather.

---

## 2. Get Your Personal Telegram User ID (Security)

To protect your personal data and prevent others from using your bot:
1. Search for **[@userinfobot](https://t.me/userinfobot)** on Telegram.
2. Send `/start`.
3. Copy the numeric **Id** (e.g. `123456789`).

---

## 3. Get Your Gemini API Key

1. Go to **[Google AI Studio](https://aistudio.google.com/app/apikey)**.
2. Create an API key for **Gemini Pro**.
3. Copy the key.

---

## 4. Configure Your Environment

1. In the project folder, copy `.env.example` to `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Open `.env` and fill in:
   ```env
   TELEGRAM_BOT_TOKEN=your_token_from_botfather
   ALLOWED_USER_ID=your_numeric_id_from_userinfobot
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-1.5-pro
   DEFAULT_CITY=Bengaluru, Karnataka, India
   ACCEPTABLE_CITIES=Bengaluru,Hyderabad,Mumbai,Pune,Ahmedabad,Gandhinagar,Remote
   ```

---

## 5. Start the Bot

Run the bot directly from PowerShell or Windows Terminal:

```powershell
python bot/main.py
```

You will see:
```
Starting AI Job Search Telegram Bot (Long-polling)...
Bot commands menu registered successfully.
```

Now open Telegram on your phone or desktop, open chat with your bot, and send:
```
/start
```

---

## 6. Available Telegram Commands

| Command | Action |
|---|---|
| `/scrape` | Search active jobs across Bengaluru, Ahmedabad, Gandhinagar, Pune, Mumbai, Hyderabad & Remote |
| `/scrape <role> <city>` | Specific search, e.g. `/scrape Python Ahmedabad` |
| `/apply <url or text>` | Evaluate job fit against your profile & tailor LaTeX CV and Cover Letter |
| `/rank` | Batch-score and rank recent postings with numeric scores |
| `/interview <role>` | Generate STAR talking points, technical prep & interview questions |
| `/report` | View application pipeline and tracker stats |
| `/status` | View active LLM, model, target cities, and system health |
| `/llm [gemini/claude]` | Switch active LLM dynamically in chat |
| `/help` | Detailed command instructions |

---

## 7. Enable Automatic 12-Hour Job Alerts (Optional)

To receive new job notifications every morning and evening without typing commands:

Open **PowerShell as Administrator** and run:
```powershell
$Action = New-ScheduledTaskAction -Execute "python" -Argument "bot/auto_scrape.py" -WorkingDirectory "C:\Users\jainish chauhan\VS Code\ai-project\ai-job-search"
$Trigger = New-ScheduledTaskTrigger -Daily -At 8am
$Trigger.Repetition = (New-ScheduledTaskTrigger -Once -At 8am -RepetitionInterval (New-TimeSpan -Hours 12) -RepetitionDuration (New-TimeSpan -Days 3650)).Repetition
Register-ScheduledTask -TaskName "AIJobSearch-AutoScrape" -Action $Action -Trigger $Trigger -Description "Runs AI Job Search Scraper every 12 hours and alerts via Telegram"
```

---

## 8. PDF Compilation Note (LaTeX)

Tailored LaTeX source files (`.tex`) are automatically generated in `cv/` and `cover_letters/`.
- If **MiKTeX** (`lualatex` / `xelatex`) is installed on your Windows PC, the bot will automatically compile and deliver `.pdf` attachments directly to your Telegram chat.
- Download MiKTeX for Windows if needed: [https://miktex.org/download](https://miktex.org/download).
