import os
import sys
import json
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Any, Optional

WATCHLIST_FILE = Path(__file__).resolve().parent.parent.parent / "watchlist.json"
if not WATCHLIST_FILE.exists():
    WATCHLIST_FILE = Path(__file__).resolve().parent.parent / "watchlist.json"

def fetch_json(url: str, headers: Optional[Dict[str, str]] = None) -> Any:
    req_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        return None

def fetch_greenhouse_jobs(company_name: str, slug: str) -> List[Dict[str, Any]]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    data = fetch_json(url)
    if not data or "jobs" not in data:
        return []

    jobs = []
    for item in data.get("jobs", []):
        title = item.get("title", "")
        job_url = item.get("absolute_url", "")
        location_obj = item.get("location", {})
        location = location_obj.get("name", "") if isinstance(location_obj, dict) else str(location_obj)
        content = item.get("content", "")
        updated_at = item.get("updated_at", "")
        date = updated_at[:10] if updated_at else None

        jobs.append({
            "id": f"gh-{slug}-{item.get('id')}",
            "title": title,
            "company": company_name,
            "location": location or "India",
            "url": job_url,
            "date": date,
            "description": content
        })
    return jobs

def fetch_lever_jobs(company_name: str, slug: str) -> List[Dict[str, Any]]:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    data = fetch_json(url)
    if not isinstance(data, list):
        return []

    jobs = []
    for item in data:
        title = item.get("text", "")
        job_url = item.get("hostedUrl", "")
        categories = item.get("categories", {})
        location = categories.get("location", "") if isinstance(categories, dict) else ""
        content = item.get("descriptionPlain", "") or item.get("description", "")
        created_at = item.get("createdAt")
        date = None
        if created_at:
            import datetime
            date = datetime.datetime.fromtimestamp(created_at / 1000.0).strftime("%Y-%m-%d")

        jobs.append({
            "id": f"lever-{slug}-{item.get('id')}",
            "title": title,
            "company": company_name,
            "location": location or "India",
            "url": job_url,
            "date": date,
            "description": content
        })
    return jobs

def filter_jobs(
    jobs: List[Dict[str, Any]],
    query: Optional[str] = None,
    location_filter: Optional[str] = None,
    max_days: Optional[int] = None
) -> List[Dict[str, Any]]:
    import datetime
    import re
    filtered = []
    
    # Parse query into OR branches (e.g. "backend developer or engineer")
    subqueries = []
    if query and query.strip():
        parts = re.split(r'\s+(?:or|OR)\s+|[,|]', query)
        subqueries = [p.strip().lower() for p in parts if p.strip()]

    loc_lower = location_filter.lower().strip() if location_filter else None
    today = datetime.date.today()

    # Target physical tech hubs in India (strictly city-based; remote is excluded)
    target_indian_cities = [
        "bangalore", "bengaluru", "hyderabad", "pune", "mumbai",
        "delhi", "gurgaon", "gurugram", "noida", "ahmedabad", "gandhinagar", "chennai"
    ]
    
    non_tech_exclusions = [
        "sales", "account executive", "recruiter", "talent acquisition",
        "human resources", "marketing", "legal counsel", "accountant", "payroll"
    ]

    for j in jobs:
        t_raw = j.get("title", "")
        t_lower = t_raw.lower()
        desc_lower = (j.get("description") or "").lower()
        title_desc = f"{t_lower} {desc_lower}"
        job_loc = (j.get("location") or "").lower()

        # 1. Location match: Strictly city-based, no remote jobs
        if "remote" in job_loc or "remote" in t_lower or "home based" in job_loc:
            continue

        if loc_lower:
            # If remote was requested as a location filter, exclude for ATS
            if loc_lower == "remote":
                continue
            if loc_lower not in job_loc:
                continue
        else:
            # Ensure role is located in one of our target Indian cities
            if not any(city in job_loc for city in target_indian_cities):
                continue

        # 2. Query / Role match:
        if subqueries:
            # Match if ANY subquery matches (OR condition)
            matched_any = False
            for sq in subqueries:
                words = sq.split()
                if all(w in title_desc for w in words):
                    matched_any = True
                    break
            if not matched_any:
                continue
        else:
            # Default target roles: Either backend developer or engineer / software engineer / SDE
            if any(ex in t_lower for ex in non_tech_exclusions):
                continue
            is_match = (
                "backend" in t_lower
                or "software engineer" in t_lower
                or "software developer" in t_lower
                or "sde" in t_lower
                or "platform engineer" in t_lower
                or "infrastructure engineer" in t_lower
                or ("engineer" in t_lower and ("backend" in title_desc or "developer" in title_desc or "software" in title_desc))
            )
            if not is_match:
                continue

        # 3. Job age (if specified and valid)
        if max_days is not None:
            job_date_str = j.get("date")
            if job_date_str:
                try:
                    job_date = datetime.date.fromisoformat(job_date_str[:10])
                    if (today - job_date).days > max_days:
                        continue
                except Exception:
                    pass

        filtered.append(j)

    return filtered

def main():
    parser = argparse.ArgumentParser(description="Company Careers Watchlist Search CLI")
    subparsers = parser.add_subparsers(dest="command")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("--query", "-q", type=str, default="")
    search_parser.add_argument("--location", "-l", type=str, default="")
    search_parser.add_argument("--limit", "-n", type=int, default=25)
    search_parser.add_argument("--jobage", type=int, default=1, help="Max job age in days (e.g. 1 for last 24 hours)")
    search_parser.add_argument("--format", type=str, choices=["json", "table", "plain"], default="json")

    args = parser.parse_args()

    if args.command == "search":
        if not WATCHLIST_FILE.exists():
            print(json.dumps({"results": [], "meta": {"count": 0}}))
            return

        with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
            watchlist = json.load(f)

        all_jobs = []
        for c in watchlist.get("companies", []):
            name = c.get("name")
            ats = c.get("ats")
            slug = c.get("slug")
            if ats == "greenhouse":
                all_jobs.extend(fetch_greenhouse_jobs(name, slug))
            elif ats == "lever":
                all_jobs.extend(fetch_lever_jobs(name, slug))

        matched = filter_jobs(all_jobs, query=args.query, location_filter=args.location, max_days=args.jobage)
        if args.limit:
            matched = matched[:args.limit]

        if args.format == "json":
            # Keep descriptions concise for search output
            output_results = []
            for item in matched:
                c = dict(item)
                if c.get("description"):
                    c["description"] = c["description"][:300] + "..."
                output_results.append(c)
            print(json.dumps({"results": output_results, "meta": {"count": len(output_results)}}))
        elif args.format == "table":
            print(f"{'Company':<15} {'Title':<40} {'Location':<20} {'URL'}")
            print("-" * 100)
            for item in matched:
                print(f"{item['company'][:14]:<15} {item['title'][:38]:<40} {item['location'][:18]:<20} {item['url']}")
        else:
            for item in matched:
                print(f"{item['company']} - {item['title']} ({item['location']})\n{item['url']}\n")

if __name__ == "__main__":
    main()
