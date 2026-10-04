# NHL Thermal Intelligence OS

NHL Thermal Intelligence OS is a Python automation project for Nordic Health & Living / Thermal Architecture market intelligence.

It reads monitoring inputs from Airtable, collects market signals, classifies and scores them, translates relevant movement into Thermal Architecture language, writes operational rows back to Airtable, and generates weekly report artifacts. Missing credentials produce setup warnings and sample/manual data keeps the system runnable.

## What v1 Does

- Uses Airtable base `appAz3gqUMa9B1myg` as the primary intelligence database.
- Reads active Sources and Keywords from Airtable when credentials are configured.
- Collects sample/manual/search/RSS signals through a source abstraction.
- Deduplicates, classifies, scores, and prioritizes signals.
- Generates TA/NHL translations, content angles, action types, and lead suggestions.
- Writes Signals, Weekly Reports, Content Ideas, Sales Leads, and System Runs to Airtable when credentials are available.
- Builds a weekly report, writes it to Google Docs when credentials are available, and always exports local Markdown, DOCX, PDF, and Excel workbook files.
- Optionally indexes Dropbox documents, sends email, and posts to Slack.
- Runs locally or on a weekly GitHub Actions schedule.

## Quick Start

1. Install Python 3.11 or newer.
2. Create a virtual environment.
3. Install dependencies with `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and fill in the credentials you have.
5. Run a health check with `python -m src.main health`.
6. Check automation readiness with `python -m src.main readiness`.
7. Check Airtable inputs with `python -m src.main setup-airtable`.
8. Run the weekly workflow with `python -m src.main run-weekly`.
9. Verify final files with `python -m src.main verify-outputs`.

The system is designed to run even before credentials are connected. It will use sample signals and print clear setup warnings.

## Core Commands

```bash
python -m src.main health
python -m src.main readiness
python -m src.main verify-outputs
python -m src.main setup-airtable
python -m src.main setup-sheets
python -m src.main collect
python -m src.main score
python -m src.main generate-report
python -m src.main index-dropbox
python -m src.main run-weekly
python -m src.main build-dashboard
```

## Primary Airtable Tables

Base: `NHL Thermal Intelligence OS`  
Base ID: `appAz3gqUMa9B1myg`

- Signals: main signal intake and scoring table.
- Actors: tracked competitors, partners, institutions, and market actors.
- Sources: active monitoring sources.
- Keywords: active monitoring keywords.
- Weekly Reports: generated report records and links.
- Content Ideas: extracted content opportunities.
- Sales Leads: extracted sales and partnership leads.
- System Runs: manual, scheduled, partial, and failed run logs.

`python -m src.main setup-airtable` checks live Airtable connectivity and reports active Sources and Keywords. Google Sheets support remains available as a secondary/manual export path through `python -m src.main setup-sheets`.

## Search Providers

Set `SEARCH_PROVIDER` to `sample`, `manual`, `serpapi`, `brave`, or `tavily`. If the provider or API key is missing, collection falls back to built-in sample signals and manual placeholders.

## Dropbox Indexing

`python -m src.main index-dropbox` indexes relevant document metadata from `DROPBOX_ROOT_PATH` when `DROPBOX_ACCESS_TOKEN` is configured. Missing Dropbox credentials produce warnings and a local empty index.

## Notifications

After report generation, `run-weekly` sends a short executive brief by email and Slack when credentials are configured. Email uses SMTP settings, including Gmail app-password SMTP when desired. Missing notification credentials only produce warnings.

## Security

Never commit credentials. Use `.env` locally and GitHub Secrets in automation. See [SECURITY.md](SECURITY.md).

## Optional Upgrades

See [ARCHITECTURE.md](ARCHITECTURE.md) for the modular design, [SETUP.md](SETUP.md) for non-technical setup steps, and [TODO.md](TODO.md) for the Phase 9 upgrade backlog.

The optional static dashboard is generated at `outputs/dashboard.html` from the latest local run.

Weekly report file exports are generated at `outputs/latest_weekly_report.md`, `outputs/latest_weekly_report.docx`, and `outputs/latest_weekly_report.pdf`.

The table-first operating workbook is generated at `outputs/master_market_intelligence_workbook.xlsx`. It is a stable master workbook: each weekly run updates the same file and carries cumulative Signals, Sales Leads, Content Ideas, Weekly Trend, and Heatmap History forward through `work/weekly_metrics_history.json`.
