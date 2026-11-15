import sys
import re
import asyncio
import importlib.util
from pathlib import Path
from typing import List, Dict, Any, Optional

from bot.config import Config
from bot.workflows.base_workflow import BaseWorkflow

# Paths
CAREERS_WATCH_PY_PATH = Config.WORKSPACE_DIR / ".agents" / "skills" / "company-careers-watch" / "cli" / "src" / "cli.py"
LINKEDIN_PY_PATH = Config.WORKSPACE_DIR / ".agents" / "skills" / "linkedin-search" / "cli" / "src" / "linkedin_py.py"

def get_careers_watch_search():
    spec = importlib.util.spec_from_file_location("cw_cli", str(CAREERS_WATCH_PY_PATH))
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return None

def get_linkedin_search_func():
    spec = importlib.util.spec_from_file_location("linkedin_py", str(LINKEDIN_PY_PATH))
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, "search_linkedin")
    raise ImportError(f"Cannot load linkedin_py from {LINKEDIN_PY_PATH}")

class ScrapeWorkflow(BaseWorkflow):
    """
    Orchestrates job discovery across Indian locations using pure-Python scrapers.
    Filters by title, city, and 1-3+ year experience parameters.
    """

    async def run(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        limit_per_city: int = 5,
        jobage_days: int = 1
    ) -> List[Dict[str, Any]]:
        # If custom query provided, split on 'or'/',' to search both; otherwise search Backend Developer, Backend Engineer & Software Engineer
        if query and query.strip():
            queries_to_run = [q.strip() for q in re.split(r'\s+(?:or|OR)\s+|[,|]', query) if q.strip()]
        else:
            queries_to_run = ["Backend Developer", "Backend Engineer", "Software Engineer"]

        target_cities = [location.strip()] if location else Config.ACCEPTABLE_CITIES

        all_results = []
        seen_urls = set()

        loop = asyncio.get_running_loop()
        search_func = get_linkedin_search_func()

        # 1. Search LinkedIn for target locations strictly posted in the last 24h across target roles
        for target_query in queries_to_run:
            for city in target_cities[:5]:  # Top priority cities
                try:
                    results = await loop.run_in_executor(
                        None,
                        lambda q=target_query, c=city: search_func(
                            query=q,
                            location=f"{c}, India" if c.lower() != "remote" else "Remote",
                            limit=limit_per_city,
                            jobage_days=jobage_days
                        )
                    )
                    for item in results:
                        url = item.get("url")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            all_results.append(item)
                except Exception as e:
                    print(f"[WARN] Failed LinkedIn scraping for query '{target_query}' in city '{city}': {e}")

        # 2. Search Company Careers Watchlist (Greenhouse, Lever ATS boards)
        cw_module = get_careers_watch_search()
        if cw_module and hasattr(cw_module, "WATCHLIST_FILE") and cw_module.WATCHLIST_FILE.exists():
            try:
                def fetch_all_cw():
                    import json
                    with open(cw_module.WATCHLIST_FILE, "r", encoding="utf-8") as f:
                        wl = json.load(f)
                    cw_jobs = []
                    for c in wl.get("companies", []):
                        name = c.get("name")
                        ats = c.get("ats")
                        slug = c.get("slug")
                        try:
                            if ats == "greenhouse":
                                cw_jobs.extend(cw_module.fetch_greenhouse_jobs(name, slug))
                            elif ats == "lever":
                                cw_jobs.extend(cw_module.fetch_lever_jobs(name, slug))
                        except Exception:
                            continue
                    
                    # For company ATS platforms, ignore 'remote' and focus strictly on physical cities
                    cw_loc = location if (location and location.strip().lower() != "remote") else None
                    return cw_module.filter_jobs(
                        cw_jobs,
                        query=query,
                        location_filter=cw_loc,
                        max_days=14  # Active openings on company boards
                    )

                cw_matched = await loop.run_in_executor(None, fetch_all_cw)
                for item in cw_matched:
                    url = item.get("url")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append({
                            "title": item.get("title"),
                            "company": item.get("company"),
                            "location": item.get("location", "India"),
                            "url": url,
                            "date": item.get("date"),
                            "portal": "company-careers"
                        })
            except Exception as e:
                print(f"[WARN] Failed Company Careers scraping: {e}")

        # 3. Sort strictly by posted_date (most recently posted first)
        def parse_sort_date(item):
            d = item.get("date")
            if d:
                return str(d)[:10]
            return "1970-01-01"

        all_results.sort(key=parse_sort_date, reverse=True)
        return all_results
