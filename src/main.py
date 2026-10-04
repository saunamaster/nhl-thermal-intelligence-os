from __future__ import annotations

import argparse
import json
from typing import Callable

from src.config_loader import AppConfig, load_config
from src.intelligence.pipeline import run_intelligence_pipeline, write_intelligence_result
from src.integrations.airtable_client import AirtableClient
from src.logger import configure_logging
from src.reporting.google_doc_reporter import GoogleDocReporter
from src.readiness import build_readiness_report, verify_required_outputs
from src.search.source_collector import collect_signals, write_collected_signals
from src.storage.dropbox_client import DropboxClient
from src.storage.google_sheets_client import GoogleSheetsClient
from src.weekly_runner import run_weekly_pipeline
from src.dashboard.dashboard_builder import build_dashboard


def health(_: argparse.Namespace) -> int:
    config = AppConfig.from_env()
    logger = configure_logging(config.log_level)
    logger.info("NHL Thermal Intelligence OS health check")

    checks = {
        "openai": bool(config.openai_api_key),
        "airtable": not config.missing_required_for_live_airtable(),
        "google_sheets": not config.missing_required_for_live_google(),
        "google_docs": bool(config.google_service_account_json and config.google_drive_folder_id),
        "dropbox": bool(config.dropbox_access_token and config.dropbox_root_path),
        "search_provider": config.search_provider or "sample",
        "email": bool(config.report_recipient_email),
        "slack": bool(config.slack_webhook_url),
    }
    print(json.dumps({"status": "ok", "checks": checks}, indent=2))
    return 0


def readiness(_: argparse.Namespace) -> int:
    config = AppConfig.from_env()
    configure_logging(config.log_level)
    print(json.dumps(build_readiness_report(config), indent=2, ensure_ascii=False))
    return 0


def verify_outputs(_: argparse.Namespace) -> int:
    configure_logging()
    result = verify_required_outputs()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["status"] == "ok" else 1


def show_config(_: argparse.Namespace) -> int:
    configure_logging()
    names = ["segments", "keywords", "sources", "scoring", "output_templates"]
    payload = {name: load_config(name) for name in names}
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def setup_sheets(_: argparse.Namespace) -> int:
    config = AppConfig.from_env()
    logger = configure_logging(config.log_level)
    result = GoogleSheetsClient(config, logger).setup_database()
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0


def setup_airtable(_: argparse.Namespace) -> int:
    config = AppConfig.from_env()
    logger = configure_logging(config.log_level)
    airtable = AirtableClient(config, logger)
    warnings = airtable.missing_warnings()
    sources = airtable.read_active_sources()
    keywords = airtable.read_active_keywords()
    print(
        json.dumps(
            {
                "status": "ok" if not warnings else "needs_credentials",
                "base_id": airtable.base_id,
                "active_sources": len(sources),
                "active_keywords": len(keywords),
                "warnings": warnings,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def score(_: argparse.Namespace) -> int:
    config = AppConfig.from_env()
    logger = configure_logging(config.log_level)
    raw_signals = collect_signals(config, logger)
    result = run_intelligence_pipeline(raw_signals, config, logger)
    output_path = write_intelligence_result(result)

    airtable_result = AirtableClient(config, logger).write_intelligence(result)

    print(
        json.dumps(
            {
                "status": "ok",
                "signals": len(result.signals),
                "content_ideas": len(result.content_ideas),
                "sales_leads": len(result.sales_leads),
                "output_path": str(output_path),
                "airtable": airtable_result.to_dict(),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def collect(_: argparse.Namespace) -> int:
    config = AppConfig.from_env()
    logger = configure_logging(config.log_level)
    signals = collect_signals(config, logger)
    output_path = write_collected_signals(signals)
    print(
        json.dumps(
            {"status": "ok", "signals": len(signals), "output_path": str(output_path)},
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def generate_report(_: argparse.Namespace) -> int:
    config = AppConfig.from_env()
    logger = configure_logging(config.log_level)
    raw_signals = collect_signals(config, logger)
    intelligence = run_intelligence_pipeline(raw_signals, config, logger)
    write_intelligence_result(intelligence)
    result = GoogleDocReporter(config, logger).publish(intelligence)
    print(
        json.dumps(
            {
                "status": "ok",
                "live": result.live,
                "title": result.title,
                "url": result.url,
                "warnings": result.warnings,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def index_dropbox(_: argparse.Namespace) -> int:
    config = AppConfig.from_env()
    logger = configure_logging(config.log_level)
    result = DropboxClient(config, logger).index_documents()
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0


def run_weekly(_: argparse.Namespace) -> int:
    config = AppConfig.from_env()
    logger = configure_logging(config.log_level)
    result = run_weekly_pipeline(config, logger)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0


def build_dashboard_command(_: argparse.Namespace) -> int:
    configure_logging()
    output_path = build_dashboard()
    print(json.dumps({"status": "ok", "dashboard_path": str(output_path)}, indent=2, ensure_ascii=False))
    return 0


def not_implemented_yet(command_name: str) -> Callable[[argparse.Namespace], int]:
    def _handler(_: argparse.Namespace) -> int:
        configure_logging().warning("%s will be implemented in a later phase.", command_name)
        print(f"{command_name} is not implemented yet. The foundation is healthy.")
        return 0

    return _handler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NHL Thermal Intelligence OS")
    subparsers = parser.add_subparsers(dest="command", required=True)

    health_parser = subparsers.add_parser("health", help="Check configuration and integration readiness.")
    health_parser.set_defaults(func=health)

    readiness_parser = subparsers.add_parser("readiness", help="Print weekly automation credential readiness.")
    readiness_parser.set_defaults(func=readiness)

    verify_outputs_parser = subparsers.add_parser("verify-outputs", help="Verify DOCX, PDF, Excel, markdown, and run summary outputs.")
    verify_outputs_parser.set_defaults(func=verify_outputs)

    config_parser = subparsers.add_parser("show-config", help="Print loaded business configuration.")
    config_parser.set_defaults(func=show_config)

    setup_parser = subparsers.add_parser("setup-sheets", help="Create or update secondary Google Sheets export tabs.")
    setup_parser.set_defaults(func=setup_sheets)

    airtable_parser = subparsers.add_parser("setup-airtable", help="Check Airtable primary database readiness and active inputs.")
    airtable_parser.set_defaults(func=setup_airtable)

    score_parser = subparsers.add_parser("score", help="Run collected signals through the intelligence pipeline.")
    score_parser.set_defaults(func=score)

    collect_parser = subparsers.add_parser("collect", help="Collect market signals from configured sources.")
    collect_parser.set_defaults(func=collect)

    report_parser = subparsers.add_parser("generate-report", help="Generate and publish the weekly report.")
    report_parser.set_defaults(func=generate_report)

    dropbox_parser = subparsers.add_parser("index-dropbox", help="Index configured Dropbox TA/NHL documents.")
    dropbox_parser.set_defaults(func=index_dropbox)

    weekly_parser = subparsers.add_parser("run-weekly", help="Run the complete weekly automation workflow.")
    weekly_parser.set_defaults(func=run_weekly)

    dashboard_parser = subparsers.add_parser("build-dashboard", help="Build optional static dashboard from latest run.")
    dashboard_parser.set_defaults(func=build_dashboard_command)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
