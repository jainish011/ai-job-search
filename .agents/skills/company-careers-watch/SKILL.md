---
name: company-careers-watch
version: 1.0.0
description: >
  Directly polls and queries company career pages and ATS platforms (Greenhouse, Lever, etc.)
  for companies on your personal watchlist. Useful for finding jobs that employers post exclusively
  on their own career sites and never publish to aggregators.
context: fork
enabled: true
allowed-tools: Bash(python .agents/skills/company-careers-watch/cli/src/cli.py *)
---

# Company Careers Watch Skill

Directly tracks and searches job openings on official company careers boards for companies
listed in `.agents/skills/company-careers-watch/watchlist.json`.

Unlike scraping HTML or relying on third-party aggregators, this queries the official, public
ATS board APIs (e.g. Greenhouse, Lever) utilized by top Indian tech employers.

## Usage

```bash
# Search for backend engineer openings across your target companies
python .agents/skills/company-careers-watch/cli/src/cli.py search -q "backend" --format table

# Return machine-readable JSON for automated ingestion
python .agents/skills/company-careers-watch/cli/src/cli.py search -q "software" --format json
```
