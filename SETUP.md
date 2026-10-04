# Setup Guide

This guide is written for an admin who wants the system running without editing code.

## 1. Prepare Airtable Access

Use the existing Airtable base as the primary intelligence database:

- Base name: `NHL Thermal Intelligence OS`
- Base ID: `appAz3gqUMa9B1myg`

Create an Airtable personal access token with access to this base and enough scope to read Sources/Keywords and create records in Signals, Weekly Reports, Content Ideas, Sales Leads, and System Runs.

Add these values locally or as GitHub configuration:

- `AIRTABLE_API_KEY`
- `AIRTABLE_BASE_ID=appAz3gqUMa9B1myg`

Check it with:

```bash
python -m src.main setup-airtable
```

## 2. Prepare Google Access

Google is now optional for live Google Docs links. Airtable is the primary database.

1. Create a Google Cloud project.
2. Enable Google Docs API and Google Drive API.
3. Create a service account.
4. Download the service account JSON key.
5. Share the target Google Drive folder with the service account email.
6. Put the full JSON value or file path into `GOOGLE_SERVICE_ACCOUNT_JSON`.
7. Put the Drive folder ID for reports into `GOOGLE_DRIVE_FOLDER_ID`.

Google Sheets is kept as a secondary/manual export path only.

## 3. Prepare OpenAI Access

1. Create an OpenAI API key.
2. Add it to `.env` as `OPENAI_API_KEY`.
3. Leave `OPENAI_MODEL` as the default unless your technical owner changes it.

If this key is missing, the system uses deterministic local fallback classification and scoring.

## 4. Optional Integrations

Dropbox:

- Add `DROPBOX_ACCESS_TOKEN`.
- Add `DROPBOX_ROOT_PATH`, such as `/Thermal Architecture`.
- Test with `python -m src.main index-dropbox`.

Search:

- Set `SEARCH_PROVIDER` to `news_rss`, `sample`, `manual`, `serpapi`, `brave`, or `tavily`.
- Add `SEARCH_API_KEY` when the selected provider requires one.
- `news_rss` collects Google News RSS results from the last seven days without a key.
  It is the default for the scheduled workflow. Results use Google News article links
  and feed summaries; they are not full article verification. Availability depends on
  the public feed. When no sources return results, the system clearly marks sample data.

Email:

- Add `REPORT_RECIPIENT_EMAIL`.
- Add SMTP settings if email should send now:
  `EMAIL_SENDER`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`.
- For Gmail SMTP, use `smtp.gmail.com`, port `587`, and an app password.

Slack:

- Add `SLACK_WEBHOOK_URL`.

## 5. First Run

Run these commands:

```bash
python -m src.main health
python -m src.main readiness
python -m src.main setup-airtable
python -m src.main run-weekly
python -m src.main verify-outputs
```

If credentials are missing, the system will keep running with sample data and tell you exactly which integrations are disabled.

When Airtable credentials are missing, the system writes local Airtable preview JSON files in `work/` and continues with sample/local inputs.

Each weekly run also writes local report files to `outputs/latest_weekly_report.md`, `outputs/latest_weekly_report.docx`, and `outputs/latest_weekly_report.pdf`.

The main overview file is `outputs/master_market_intelligence_workbook.xlsx`. Use this one master workbook for filtering, table review, heatmap overview, pie charts, and trend tracking over time. The local history file `work/weekly_metrics_history.json` is updated each run and feeds the workbook's cumulative `Signals`, `Sales Leads`, `Content Ideas`, `Weekly Trend`, and `Chart Data` tabs.

## 6. GitHub Actions

The scheduled workflow runs every Monday at 06:00 UTC. It can also be started manually from the GitHub Actions tab.

The workflow prints credential readiness before it runs and verifies that these files exist after it runs:

- `outputs/latest_weekly_report.md`
- `outputs/latest_weekly_report.docx`
- `outputs/latest_weekly_report.pdf`
- `outputs/master_market_intelligence_workbook.xlsx`
- `work/weekly_run_summary.json`

The generated DOCX, PDF, Excel workbook, Markdown report, JSON work files, logs, and dashboard are uploaded as the `weekly-market-intelligence-artifacts` artifact.

Each run restores `weekly_metrics_history.json` from the latest
`market-intelligence-master-history` artifact before generating the master workbook.
After output verification, it saves the updated history for the next run. Both artifact
types are retained for 90 days (subject to repository retention limits). Download a
backup before pausing automation for longer than this period. The workflow stops if
it finds expired history, rather than silently starting a new master document.

The public repository must contain only code and configuration examples. Keep `.env`,
credentials, generated reports, and intelligence history out of Git. Report artifacts
require GitHub sign-in to download; their local paths are not public Airtable links.

Runs containing sample signals have status `partial` and explicitly identify test data
in the run summary. Missing OpenAI credentials are also reported; local rules remain
available as a fallback. A successful process exit alone does not confirm live monitoring.

Repeated runs skip existing Signals (source URL and title), Content Ideas (title and
source signal), Sales Leads (name, organization and website), and Weekly Reports
(title and creation date). Existing records and human review statuses are preserved.
Each invocation still creates a separate System Runs entry. Older duplicate records
are preserved for review rather than deleted automatically.

Add this GitHub Secret for the live Airtable database:

- `AIRTABLE_API_KEY`

Add this GitHub repository Variable:

- `AIRTABLE_BASE_ID=appAz3gqUMa9B1myg`

Optional GitHub Secrets for live Google Docs output:

- `GOOGLE_SERVICE_ACCOUNT_JSON`
- `GOOGLE_DRIVE_FOLDER_ID`

Recommended for AI-quality classification and scoring:

- `OPENAI_API_KEY`

Optional integration secrets:

- `DROPBOX_ACCESS_TOKEN`
- `DROPBOX_ROOT_PATH`
- `SEARCH_API_KEY`
- `REPORT_RECIPIENT_EMAIL`
- `SLACK_WEBHOOK_URL`
- `EMAIL_SENDER`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`

Add these GitHub repository Variables when you want to override defaults:

- `OPENAI_MODEL`
- `SEARCH_PROVIDER`
- `REPORT_LANGUAGE`
