from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_dotenv(path: Path | None = None) -> None:
    """Load simple KEY=VALUE pairs from .env when python-dotenv is unavailable."""
    env_path = path or PROJECT_ROOT / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data or {}
    except ModuleNotFoundError:
        return _minimal_yaml(path.read_text(encoding="utf-8"))


def _minimal_yaml(text: str) -> dict[str, Any]:
    """Tiny YAML reader for the simple config files in this repository."""
    lines = [
        (len(raw_line) - len(raw_line.lstrip(" ")), raw_line.strip())
        for raw_line in text.splitlines()
        if raw_line.strip() and not raw_line.lstrip().startswith("#")
    ]
    value, _ = _parse_yaml_block(lines, 0, 0)
    return value if isinstance(value, dict) else {}


def _parse_yaml_block(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    if index >= len(lines):
        return {}, index

    first_indent, first_text = lines[index]
    if first_indent < indent:
        return {}, index

    if first_text.startswith("- "):
        values: list[Any] = []
        while index < len(lines):
            line_indent, text = lines[index]
            if line_indent != indent or not text.startswith("- "):
                break
            item_text = text[2:].strip()
            if not item_text:
                child, index = _parse_yaml_block(lines, index + 1, indent + 2)
                values.append(child)
                continue
            if ":" in item_text:
                key, raw_value = item_text.split(":", 1)
                item: dict[str, Any] = {}
                if raw_value.strip():
                    item[key.strip()] = _parse_scalar(raw_value.strip())
                    index += 1
                else:
                    child, index = _parse_yaml_block(lines, index + 1, indent + 2)
                    item[key.strip()] = child
                while index < len(lines) and lines[index][0] == indent + 2:
                    child_text = lines[index][1]
                    if ":" not in child_text:
                        break
                    child_key, child_raw_value = child_text.split(":", 1)
                    if child_raw_value.strip():
                        item[child_key.strip()] = _parse_scalar(child_raw_value.strip())
                        index += 1
                    else:
                        child, index = _parse_yaml_block(lines, index + 1, indent + 4)
                        item[child_key.strip()] = child
                values.append(item)
                continue
            values.append(_parse_scalar(item_text))
            index += 1
        return values, index

    values: dict[str, Any] = {}
    while index < len(lines):
        line_indent, text = lines[index]
        if line_indent != indent or text.startswith("- ") or ":" not in text:
            break
        key, raw_value = text.split(":", 1)
        if raw_value.strip():
            values[key.strip()] = _parse_scalar(raw_value.strip())
            index += 1
            continue
        child, index = _parse_yaml_block(lines, index + 1, indent + 2)
        values[key.strip()] = child
    return values, index


def _parse_scalar(value: str) -> Any:
    value = value.strip().strip('"').strip("'")
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


@dataclass(frozen=True)
class AppConfig:
    openai_api_key: str
    openai_model: str
    google_service_account_json: str
    google_drive_folder_id: str
    google_sheet_id: str
    dropbox_access_token: str
    dropbox_root_path: str
    search_provider: str
    search_api_key: str
    report_recipient_email: str
    slack_webhook_url: str
    report_language: str
    log_level: str
    email_sender: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    airtable_api_key: str = ""
    airtable_base_id: str = "appAz3gqUMa9B1myg"

    @classmethod
    def from_env(cls) -> "AppConfig":
        load_dotenv()
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            google_service_account_json=os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", ""),
            google_drive_folder_id=os.getenv("GOOGLE_DRIVE_FOLDER_ID", ""),
            google_sheet_id=os.getenv("GOOGLE_SHEET_ID", ""),
            dropbox_access_token=os.getenv("DROPBOX_ACCESS_TOKEN", ""),
            dropbox_root_path=os.getenv("DROPBOX_ROOT_PATH", ""),
            search_provider=os.getenv("SEARCH_PROVIDER", "sample"),
            search_api_key=os.getenv("SEARCH_API_KEY", ""),
            report_recipient_email=os.getenv("REPORT_RECIPIENT_EMAIL", ""),
            slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL", ""),
            report_language=os.getenv("REPORT_LANGUAGE", "da"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            email_sender=os.getenv("EMAIL_SENDER", ""),
            smtp_host=os.getenv("SMTP_HOST", ""),
            smtp_port=int(os.getenv("SMTP_PORT", "587") or "587"),
            smtp_username=os.getenv("SMTP_USERNAME", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            airtable_api_key=os.getenv("AIRTABLE_API_KEY", ""),
            airtable_base_id=os.getenv("AIRTABLE_BASE_ID", "appAz3gqUMa9B1myg"),
        )

    def missing_required_for_live_airtable(self) -> list[str]:
        missing = []
        if not self.airtable_api_key:
            missing.append("AIRTABLE_API_KEY")
        if not self.airtable_base_id:
            missing.append("AIRTABLE_BASE_ID")
        return missing

    def missing_required_for_live_google(self) -> list[str]:
        missing = []
        if not self.google_service_account_json:
            missing.append("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not self.google_sheet_id:
            missing.append("GOOGLE_SHEET_ID")
        return missing

    def service_account_info(self) -> dict[str, Any] | None:
        if not self.google_service_account_json:
            return None
        value = self.google_service_account_json.strip()
        possible_path = Path(value)
        if possible_path.exists():
            return json.loads(possible_path.read_text(encoding="utf-8"))
        return json.loads(value)


def load_config(name: str) -> dict[str, Any]:
    return load_yaml_file(PROJECT_ROOT / "config" / f"{name}.yml")
