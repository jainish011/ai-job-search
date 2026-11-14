# Automated 12-Hour Job Alert Setup (Windows Task Scheduler)

You can run `bot/auto_scrape.py` automatically twice a day (e.g. 8:00 AM and 8:00 PM). It will check for newly posted roles and deliver them straight to your phone on Telegram.

---

## ⚡ Option 1: One-Line PowerShell Command (Recommended)

Open **PowerShell as Administrator** and paste this command:

```powershell
$Action = New-ScheduledTaskAction -Execute "python" -Argument "bot/auto_scrape.py" -WorkingDirectory "C:\Users\jainish chauhan\VS Code\ai-project\ai-job-search"
$Trigger = New-ScheduledTaskTrigger -Daily -At 8am
$Trigger.Repetition = (New-ScheduledTaskTrigger -Once -At 8am -RepetitionInterval (New-TimeSpan -Hours 12) -RepetitionDuration (New-TimeSpan -Days 3650)).Repetition
Register-ScheduledTask -TaskName "AIJobSearch-AutoScrape" -Action $Action -Trigger $Trigger -Description "Runs AI Job Search Scraper every 12 hours and alerts via Telegram"
```

---

## 🖥️ Option 2: GUI Setup (Task Scheduler)

1. Press `Win + R`, type `taskschd.msc`, and press **Enter**.
2. Click **Create Task...** on the right sidebar.
3. In **General**:
   - Name: `AIJobSearch-AutoScrape`
   - Check *"Run only when user is logged on"*
4. In **Triggers**:
   - Click **New...**
   - Begin the task: **On a schedule**
   - Daily at: `8:00:00 AM`
   - Under Advanced settings: Check **Repeat task every**: `12 hours` for a duration of: `Indefinitely`
   - Click **OK**.
5. In **Actions**:
   - Click **New...**
   - Program/script: `python`
   - Add arguments: `bot/auto_scrape.py`
   - Start in: `C:\Users\jainish chauhan\VS Code\ai-project\ai-job-search`
   - Click **OK**.
6. Click **OK** to save the task.

---

## 🧪 Testing the Task

To test it immediately at any time, run:
```powershell
python bot/auto_scrape.py
```
If new jobs are found, your Telegram bot will ping your phone with the alert.
