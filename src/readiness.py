from __future__ import annotations

from pathlib import Path
from typing import Any

from src.config_loader import AppConfig


LIVE_AIRTABLE_SECRETS = [
    "AIRTABLE_API_KEY",
    "AIRTABLE_BASE_ID",
]

LIVE_GOOGLE_SECRETS = [
    "GOOGLE_SERVICE_ACCOUNT_JSON",
    "GOOGLE_DRIVE_FOLDER_ID",
]

RECOMMENDED_SECRETS = [
    "OPENAI_API_KEY",
]

OPTIONAL_INTEGRATION_SECRETS = [
    "DROPBOX_ACCESS_TOKEN",
    "DROPBOX_ROOT_PATH",
    "SEARCH_API_KEY",
    "REPORT_RECIPIENT_EMAIL",
    "SLACK_WEBHOOK_URL",
    "EMAIL_SENDER",
    "SMTP_HOST",
    "SMTP_USERNAME",
    "SMTP_PASSWORD",
]

REQUIRED_OUTPUTS = {
    "weekly_report_markdown": Path("outputs") / "latest_weekly_report.md",
    "weekly_report_docx": Path("outputs") / "latest_weekly_report.docx",
    "weekly_report_pdf": Path("outputs") / "latest_weekly_report.pdf",
    "market_intelligence_workbook": Path("outputs") / "master_market_intelligence_workbook.xlsx",
    "weekly_run_summary": Path("work") / "weekly_run_summary.json",
}


def build_readiness_report(config: AppConfig) -> dict[str, Any]:
    missing_live_airtable = _missing(config, LIVE_AIRTABLE_SECRETS)
    missing_live_google = _missing(config, LIVE_GOOGLE_SECRETS)
    missing_recommended = _missing(config, RECOMMENDED_SECRETS)
    missing_optional = _missing(config, OPTIONAL_INTEGRATION_SECRETS)

    search_provider = (config.search_provider or "sample").lower()
    live_search_ready = search_provider == "news_rss" or (
        search_provider in {"serpapi", "brave", "tavily"} and bool(config.search_api_key)
    )
    email_ready = bool(config.report_recipient_email and config.email_sender and config.smtp_host and config.smtp_username and config.smtp_password)

    return {
        "status": "ready" if not missing_live_airtable else "needs_credentials",
        "core_weekly_run": "ready",
        "live_airtable_database": "ready" if not missing_live_airtable else "not_ready",
        "live_google_docs": "ready" if not missing_live_google else "not_ready",
        "integrations": {
            "openai": bool(config.openai_api_key),
            "airtable": bool(config.airtable_api_key and config.airtable_base_id),
            "google_sheets": bool(config.google_service_account_json and config.google_sheet_id),
            "google_docs": bool(config.google_service_account_json and config.google_drive_folder_id),
            "dropbox": bool(config.dropbox_access_token and config.dropbox_root_path),
            "search_provider": search_provider,
            "search": live_search_ready,
            "email": email_ready,
            "slack": bool(config.slack_webhook_url),
        },
        "missing_required_for_live_airtable_database": missing_live_airtable,
        "missing_optional_for_live_google_docs": missing_live_google,
        "missing_recommended_for_ai_quality": missing_recommended,
        "missing_optional_integrations": missing_optional,
        "notes": [
            "Core weekly runs continue with sample/local fallbacks when credentials are missing.",
            "Airtable is the primary operational database for Sources, Keywords, Signals, Weekly Reports, Content Ideas, Sales Leads, and System Runs.",
            "Live Google Docs output requires the Google service account and Drive folder ID; Google Sheets is no longer the primary database.",
            "Email, Slack, Dropbox, and paid search providers are optional and do not block the weekly run.",
        ],
    }


def verify_required_outputs(base_path: Path | None = None) -> dict[str, Any]:
    base_path = base_path or Path(".")
    artifacts = []
    missing_or_invalid = []

    for name, path in REQUIRED_OUTPUTS.items():
        detail = _artifact_detail(name, base_path / path)
        artifacts.append(detail)
        if not detail["valid"]:
            missing_or_invalid.append(name)

    return {
        "status": "ok" if not missing_or_invalid else "missing_outputs",
        "missing_or_invalid": missing_or_invalid,
        "artifacts": artifacts,
    }


def _artifact_detail(name: str, path: Path) -> dict[str, Any]:
    exists = path.exists()
    size = path.stat().st_size if exists else 0
    valid = exists and size > 0 and _has_expected_signature(path)
    return {
        "name": name,
        "path": str(path),
        "exists": exists,
        "size_bytes": size,
        "valid": valid,
    }


def _has_expected_signature(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return path.read_text(encoding="utf-8", errors="ignore").lstrip().startswith("{")
    if suffix == ".md":
        return path.stat().st_size > 0

    with path.open("rb") as file:
        prefix = file.read(4)
    if suffix in {".docx", ".xlsx"}:
        return prefix == b"PK\x03\x04"
    if suffix == ".pdf":
        return prefix == b"%PDF"
    return path.stat().st_size > 0


def _missing(config: AppConfig, names: list[str]) -> list[str]:
    values = {
        "OPENAI_API_KEY": config.openai_api_key,
        "GOOGLE_SERVICE_ACCOUNT_JSON": config.google_service_account_json,
        "GOOGLE_SHEET_ID": config.google_sheet_id,
        "GOOGLE_DRIVE_FOLDER_ID": config.google_drive_folder_id,
        "DROPBOX_ACCESS_TOKEN": config.dropbox_access_token,
        "DROPBOX_ROOT_PATH": config.dropbox_root_path,
        "SEARCH_API_KEY": config.search_api_key,
        "REPORT_RECIPIENT_EMAIL": config.report_recipient_email,
        "SLACK_WEBHOOK_URL": config.slack_webhook_url,
        "EMAIL_SENDER": config.email_sender,
        "SMTP_HOST": config.smtp_host,
        "SMTP_USERNAME": config.smtp_username,
        "SMTP_PASSWORD": config.smtp_password,
        "AIRTABLE_API_KEY": config.airtable_api_key,
        "AIRTABLE_BASE_ID": config.airtable_base_id,
    }
    return [name for name in names if not values.get(name)]
