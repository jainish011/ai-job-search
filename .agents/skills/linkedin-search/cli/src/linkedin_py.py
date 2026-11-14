import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional

def search_linkedin(
    query: str,
    location: str,
    limit: int = 15,
    jobage_days: Optional[int] = 14
) -> List[Dict[str, Any]]:
    """
    Query LinkedIn unauthenticated guest API directly in Python.
    Works anywhere without needing bun or Node.js.
    """
    encoded_q = urllib.parse.quote_plus(query)
    encoded_loc = urllib.parse.quote_plus(location)
    
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_q}&location={encoded_loc}&start=0"
    if jobage_days:
        # LinkedIn uses f_TPR=r{seconds}
        seconds = jobage_days * 86400
        url += f"&f_TPR=r{seconds}"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )

    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            html = response.read().decode("utf-8")
    except Exception as e:
        print(f"[WARN] LinkedIn query error: {e}", file=sys.stderr)
        return []

    soup = BeautifulSoup(html, "html.parser")
    cards = soup.find_all("li")
    jobs = []

    for c in cards:
        t_el = c.find("h3", class_="base-search-card__title")
        comp_el = c.find("h4", class_="base-search-card__subtitle")
        loc_el = c.find("span", class_="job-search-card__location")
        link_el = c.find("a", class_="base-card__full-link")
        time_el = c.find("time")

        if t_el and comp_el:
            title = t_el.get_text(strip=True)
            company = comp_el.get_text(strip=True)
            loc = loc_el.get_text(strip=True) if loc_el else location
            href = link_el["href"].split("?")[0] if link_el and "href" in link_el.attrs else ""
            date_val = time_el.get("datetime") if time_el and time_el.has_attr("datetime") else None

            jobs.append({
                "title": title,
                "company": company,
                "location": loc,
                "url": href,
                "date": date_val,
                "portal": "linkedin"
            })

            if len(jobs) >= limit:
                break

    return jobs

def main():
    parser = argparse.ArgumentParser(description="LinkedIn Search CLI (Pure Python)")
    subparsers = parser.add_subparsers(dest="command")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("--query", "-q", type=str, default="Backend Engineer")
    search_parser.add_argument("--location", "-l", type=str, default="Bengaluru, Karnataka, India")
    search_parser.add_argument("--limit", "-n", type=int, default=15)
    search_parser.add_argument("--jobage", type=int, default=14)
    search_parser.add_argument("--format", type=str, choices=["json", "table"], default="json")

    args = parser.parse_args()

    if args.command == "search":
        results = search_linkedin(
            query=args.query,
            location=args.location,
            limit=args.limit,
            jobage_days=args.jobage
        )
        if args.format == "json":
            print(json.dumps({"results": results, "meta": {"count": len(results)}}))
        else:
            print(f"{'Company':<20} {'Title':<40} {'Location':<25}")
            print("-" * 85)
            for r in results:
                print(f"{r['company'][:18]:<20} {r['title'][:38]:<40} {r['location'][:23]:<25}")

if __name__ == "__main__":
    main()
