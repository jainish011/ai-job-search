import asyncio
import sys
sys.path.append('.')
from bot.workflows.scrape_workflow import ScrapeWorkflow

async def test():
    wf = ScrapeWorkflow()
    jobs = await wf.run('Software Engineer', limit_per_city=3, jobage_days=1)
    print(f"Total jobs fetched (last 24h): {len(jobs)}")
    for j in jobs[:6]:
        print(f"• [{j.get('date')}] {j.get('title')} at {j.get('company')} ({j.get('location')})")

if __name__ == "__main__":
    asyncio.run(test())
