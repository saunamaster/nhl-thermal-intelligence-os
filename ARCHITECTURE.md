# Architecture

NHL Thermal Intelligence OS is organized as a modular pipeline. Each module can run with live credentials or fall back to local/sample behavior.

## Pipeline

1. Load config and environment.
2. Load active Sources and Keywords from Airtable, falling back to local config/sample data when credentials are missing.
3. Collect signals from search, RSS, manual config, or sample data.
4. Deduplicate by normalized title, URL, and text fingerprint.
5. Classify by segment, category, actor, and action type.
6. Score strategic relevance, commercial opportunity, authority, competition threat, and TA gap.
7. Translate market language into TA/NHL positioning.
8. Generate content angles and sales leads.
9. Write Signals, Weekly Reports, Content Ideas, Sales Leads, and System Runs to Airtable when available.
10. Build and publish a weekly Google Docs report when available.
11. Send optional email and Slack notifications.

## Modules

- `src/search`: search provider abstraction, RSS collection, source orchestration.
- `src/intelligence`: classification, scoring, deduplication, TA translation, content and lead generation.
- `src/integrations`: Airtable operational database client and future integration clients.
- `src/storage`: Google Sheets secondary export support, Google Docs, Google Drive, and Dropbox clients.
- `src/reporting`: weekly report construction and delivery.
- `src/models`: dataclasses for signals, actors, and reports.
- `src/utils`: date, text, and URL helpers.

## Fallback Strategy

Every integration has a no-credential path:

- Airtable: writes local preview JSON files and falls back to local/sample inputs.
- Google Sheets: secondary/manual export path only.
- Google Docs: stores a local report preview path in the run result.
- OpenAI: uses deterministic keyword-based classification and scoring.
- Search: uses sample and manual sources.
- Dropbox: logs a disabled warning.
- Email/Slack: logs skipped delivery.

## Configuration

Business configuration lives in `config/*.yml`. Prompts live in `prompts/*.md`. Credentials live only in environment variables.

## Airtable Primary Database

Airtable base `appAz3gqUMa9B1myg` is the operational database. Its tables are:

- Signals
- Actors
- Sources
- Keywords
- Weekly Reports
- Content Ideas
- Sales Leads
- System Runs

Google Sheets is no longer the primary database. The Excel workbook remains a generated reporting artifact for table review, statistics, heatmap analysis, and charts.

## Phase 9 Roadmap

Future upgrades can add:

- A dashboard for signal review and assignment.
- CRM sync from approved Airtable Sales Leads.
- Advanced search APIs and saved competitor profile pages.
- Team routing by segment and action type.
- Analytics for language ownership, lead source quality, and report outcomes.

The repository includes a lightweight static dashboard generator and extension stubs for CRM sync and team routing. These remain outside the weekly core path until the Airtable primary workflow is stable with live credentials.
