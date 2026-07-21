# Opportunity Radar v3

A local opportunity-intelligence and job-hunt CRM.

## Run on Windows
1. Install Python 3.11+.
2. Extract the ZIP.
3. Double-click `run.bat`.
4. Open `http://127.0.0.1:8000`.

## What v3 adds
- Personal profile and skill-based match scoring
- Concurrent public website crawling
- GitHub organization/repository analysis
- Job-post extraction and skill matching
- Company score history and change events
- Contacts and outreach CRM
- Follow-ups and activity timeline
- Saved discovery campaigns
- Daily scheduler while the application is running
- Rule-based personalized email and LinkedIn drafts
- Pipeline, jobs, analytics, settings, exports and JSON API

## Responsible use
Use public company information only. Respect website terms, robots.txt and rate limits.
Do not scrape LinkedIn or guess private email addresses. Review every outreach message.


## v0.4.0 + v0.5.0

The project now includes environment-based configuration, logging, Alembic migrations,
tests, maintenance commands, and a multi-query discovery engine with deduplication and
campaign run history. See `INSTALL_V040_V050.md` for upgrade instructions.
