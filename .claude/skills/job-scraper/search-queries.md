# Search Queries for Job Scraper

<!-- SETUP: Customize these queries based on your skills, target roles, and location -->

## Installed portal CLIs (primary for `/scrape`)

`/scrape` discovers every portal skill under `.agents/skills/*/SKILL.md` and runs its CLI first. Shipped country-agnostic CLIs include `linkedin-search` and `freehire-search`; Danish demos and any skill you add with `/add-portal` are included the same way. You do **not** need a matching `site:` line below for those CLIs to run.

The `site:` query templates in this file are the **WebSearch fallback** — for portals without a CLI, company career pages, or when a CLI fails.

**Language scope:** write every query category in every language listed in your CLAUDE.md Languages table (typically 1-2, sometimes more). A posting requiring a language you have *not* declared, as a job condition, is excluded before scoring; a posting requiring a *higher level* than you declared in a language you *do* work in is flagged for your own judgment, not excluded — see `04-job-evaluation.md`'s Language Gate, the single source of truth for this rule. Translate each category's keywords rather than machine-translating word-for-word (e.g. "Frontend Developer" -> "Desarrollador Frontend", not a literal word-for-word translation) if you work in more than one language.

## Search Sites

Primary (Indian & Global tech job boards):
- **LinkedIn (jobs-guest unauthenticated)** - Pure-Python scraper active for Bengaluru, Ahmedabad, Gandhinagar, Pune, Mumbai, Hyderabad, Remote
- **Company Careers Watch** - Direct ATS queries for 12+ Indian tech employers (`.agents/skills/company-careers-watch/watchlist.json`)
- **freehire.me** - Multi-market ATS aggregator

Secondary (company career pages via Google):
- Direct Google searches with `site:` filters for known target companies

## Query Categories

### Priority 1: Backend & Software Engineering (Core)

These match your strongest and most desired career direction (1–3+ years experience).

#### Plain terms (portal CLIs)

```
Backend Engineer
Software Engineer
Python Developer
Backend Developer
```

#### WebSearch-only (`site:` fallback)

```
site:linkedin.com/jobs "Backend Engineer" "Bengaluru" OR "Ahmedabad" OR "Gandhinagar" OR "Pune" OR "Remote"
site:linkedin.com/jobs "Software Engineer" "India"
site:boards.greenhouse.io "Backend Engineer" "India"
site:jobs.lever.co "Software Engineer" "India"
```
```

### Priority 2: [YOUR_DOMAIN_EXPERTISE]

These match your domain expertise.

#### Plain terms (portal CLIs)

```
[YOUR_DOMAIN_KEYWORD_1]
[YOUR_DOMAIN_KEYWORD_2]
```

#### WebSearch-only (`site:` fallback)

```
site:[YOUR_JOB_BOARD] [YOUR_DOMAIN_KEYWORD_1] [YOUR_CITY] OR [YOUR_REGION]
site:[YOUR_JOB_BOARD] [YOUR_DOMAIN_KEYWORD_2] [YOUR_COUNTRY]
site:linkedin.com/jobs [YOUR_DOMAIN_KEYWORD_1] [YOUR_CITY] [YOUR_COUNTRY]
```

### Priority 3: [YOUR_ADJACENT_ROLE_TYPE]

Adjacent roles you could pivot into.

#### Plain terms (portal CLIs)

```
[YOUR_ADJACENT_TITLE_1]
[YOUR_ADJACENT_TITLE_2]
```

#### WebSearch-only (`site:` fallback)

```
site:[YOUR_JOB_BOARD] "[YOUR_ADJACENT_TITLE_1]" [YOUR_KEY_SKILL] [YOUR_CITY]
site:[YOUR_JOB_BOARD] "[YOUR_ADJACENT_TITLE_2]" [YOUR_KEY_SKILL] [YOUR_CITY]
```

### Priority 4: Broader Technical / Consulting

Wider net for general technical roles.

#### Plain terms (portal CLIs)

```
[YOUR_KEY_SKILL] developer
technical consultant
```

#### WebSearch-only (`site:` fallback)

```
site:[YOUR_JOB_BOARD] [YOUR_KEY_SKILL] developer [YOUR_CITY]
site:linkedin.com/jobs "[YOUR_KEY_SKILL] developer" [YOUR_CITY]
site:[YOUR_JOB_BOARD] "technical consultant" [YOUR_DOMAIN] [YOUR_CITY]
```

## Location Filter

When evaluating results, verify the job location is within reasonable commute distance from your home. Define acceptable areas:
- [YOUR_CITY] and surrounding areas
- [ACCEPTABLE_AREA_1]
- [ACCEPTABLE_AREA_2]
- [BORDERLINE_AREA] (borderline - ~X min by transit)
- [TOO_FAR_AREA] (too far)

## Language Filter

Your working languages and levels are in CLAUDE.md's Languages table. When filtering scraped results, apply `04-job-evaluation.md`'s Language Gate: a posting requiring a language you haven't declared at all is excluded; a posting requiring a higher level than you declared in a language you do work in is not excluded, flag it clearly instead (see `job-scraper/SKILL.md`'s Step 3 "Quick Fit Assessment" for how the flag surfaces in `/scrape` output). Postings simply *written* in a language you don't work in, that don't require it on the job, are fine.

## Date Filter

Only include jobs posted within the last 14 days, matching `/scrape` Step 1b.3: use a supported recency filter or filter the returned publication dates client-side. A future application deadline does not bypass this discovery window; `/rank` handles deadline expiry and urgency separately after discovery. If a posting date cannot be determined, include it but flag as "date unknown".

## Adapting Queries

If the user specifies a focus area, select queries from the matching category and also generate 2-3 custom queries for that focus. For example:
- "/scrape [focus_area]" -> relevant category queries + custom focus-specific queries
