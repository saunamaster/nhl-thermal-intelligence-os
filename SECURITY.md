# Security

## Credential Rules

- Do not commit `.env`, service account files, API tokens, OAuth tokens, or credentials.
- Use environment variables locally and GitHub Secrets in automation.
- Rotate credentials immediately if they are pasted into chat, committed, or shared in the wrong place.

## Airtable Access

Use an Airtable personal access token with the least access needed for base `appAz3gqUMa9B1myg`:

- Read Sources and Keywords.
- Create Signals, Weekly Reports, Content Ideas, Sales Leads, and System Runs.
- Update records only if later review workflows explicitly need it.

Store the token only in `.env` locally or GitHub Secrets as `AIRTABLE_API_KEY`.

## Google Access

Use a dedicated Google service account with the least access needed:

- Google Docs API for reports.
- Google Drive API only for creating reports in the configured folder.

Share only the target Drive folder with the service account. Google Sheets is no longer the primary intelligence database.

## OpenAI Access

Use a project-scoped API key. The system sends market-signal text for classification, scoring, translation, and report drafting. Do not send confidential customer data unless approved.

## Optional Integrations

Dropbox, Gmail/email, Slack, Google Docs, Google Sheets secondary export, and search APIs are optional. Leave their environment variables blank to disable them. If SMTP is used, prefer app passwords or scoped service credentials and rotate them like API keys.

## Guardrails

Reports and generated text must not claim medical, legal, ISO, compliance, health, safety, or revenue guarantees unless formally verified. Use standards-aware and certification-readiness language where appropriate.

## GitHub Actions

Store all secrets in GitHub Secrets. The workflow is designed so missing optional secrets do not break the full run.
