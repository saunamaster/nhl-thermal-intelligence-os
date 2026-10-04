from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.config_loader import AppConfig
from src.intelligence.pipeline import run_intelligence_pipeline, write_intelligence_result
from src.integrations.airtable_client import AirtableClient
from src.reporting.google_doc_reporter import GoogleDocReporter
from src.reporting.notification_service import send_notifications
from src.search.source_collector import collect_signals, write_collected_signals
from src.storage.dropbox_client import DropboxClient


@dataclass
class WeeklyRunResult:
    status: str
    collected_signals: int = 0
    scored_signals: int = 0
    content_ideas: int = 0
    sales_leads: int = 0
    report_url: str = ""
    notifications: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    outputs: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "collected_signals": self.collected_signals,
            "scored_signals": self.scored_signals,
            "content_ideas": self.content_ideas,
            "sales_leads": self.sales_leads,
            "report_url": self.report_url,
            "notifications": self.notifications,
            "warnings": self.warnings,
            "outputs": self.outputs,
        }


def run_weekly_pipeline(config: AppConfig, logger: logging.Logger) -> WeeklyRunResult:
    warnings: list[str] = []
    outputs: dict[str, str] = {}
    airtable = AirtableClient(config, logger)

    warnings.extend(airtable.missing_warnings())
    if not config.openai_api_key:
        warnings.append("OPENAI_API_KEY is missing; classification uses local rules rather than OpenAI.")

    try:
        dropbox_result = DropboxClient(config, logger).index_documents()
        outputs["dropbox_index"] = dropbox_result.output_path
        warnings.extend(dropbox_result.warnings)
    except Exception as exc:
        warnings.append(f"Dropbox indexing failed but workflow continued: {exc}")
        logger.warning(warnings[-1])

    raw_signals = collect_signals(config, logger)
    sample_count = sum(signal.source_url.startswith("sample://") for signal in raw_signals)
    if sample_count:
        warnings.append(f"Test data: {sample_count} of {len(raw_signals)} collected signals are samples.")
    outputs["collected_signals"] = str(write_collected_signals(raw_signals))
    intelligence = run_intelligence_pipeline(raw_signals, config, logger)
    outputs["intelligence_result"] = str(write_intelligence_result(intelligence))

    try:
        airtable_result = airtable.write_intelligence(intelligence)
        if airtable_result.output_path:
            outputs["airtable_intelligence_preview"] = airtable_result.output_path
        warnings.extend(airtable_result.warnings)
    except Exception as exc:
        warnings.append(f"Airtable intelligence write failed but workflow continued: {exc}")
        logger.warning(warnings[-1])

    try:
        report_result = GoogleDocReporter(config, logger).publish(intelligence)
        report_url = report_result.url
        outputs.update(
            {
                "weekly_report_markdown": report_result.artifacts.markdown_path,
                "weekly_report_docx": report_result.artifacts.docx_path,
                "weekly_report_pdf": report_result.artifacts.pdf_path,
                "market_intelligence_workbook": report_result.artifacts.xlsx_path,
            }
        )
        warnings.extend(report_result.warnings)
    except Exception as exc:
        report_url = ""
        warnings.append(f"Report generation failed: {exc}")
        logger.exception("Report generation failed")

    notifications = []
    if report_url:
        delivery_results = send_notifications(config, report_result.title, report_url, intelligence, logger)
        notifications = [result.to_dict() for result in delivery_results]
        warnings.extend(result.warning for result in delivery_results if result.warning)

    result = WeeklyRunResult(
        status="ok" if (
            report_url and not sample_count and airtable.is_configured() and config.openai_api_key
            and not any("Airtable" in warning and "failed" in warning for warning in warnings)
        ) else "partial",
        collected_signals=len(raw_signals),
        scored_signals=len(intelligence.signals),
        content_ideas=len(intelligence.content_ideas),
        sales_leads=len(intelligence.sales_leads),
        report_url=report_url,
        notifications=notifications,
        warnings=_dedupe_warnings(warnings),
        outputs=outputs,
    )
    try:
        system_run = airtable.log_system_run(
            run_name=f"NHL Thermal Intelligence OS - Week {outputs.get('weekly_report_markdown', 'local run')}",
            run_type="weekly scheduled",
            status=result.status,
            signals_collected=result.collected_signals,
            signals_scored=result.scored_signals,
            reports_generated=1 if report_url else 0,
            generated_files=outputs,
            warnings=result.warnings,
            next_action=_next_action(result.warnings),
        )
        if system_run.output_path:
            outputs["airtable_system_run_preview"] = system_run.output_path
        warnings.extend(system_run.warnings)
        result.warnings = _dedupe_warnings(warnings)
        result.outputs = outputs
    except Exception as exc:
        result.status = "partial"
        result.warnings = _dedupe_warnings(result.warnings + [f"Airtable System Runs logging failed: {exc}"])
        logger.warning(result.warnings[-1])
    _write_run_summary(result)
    return result


def _write_run_summary(result: WeeklyRunResult) -> Path:
    path = Path("work") / "weekly_run_summary.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _dedupe_warnings(warnings: list[str]) -> list[str]:
    deduped: list[str] = []
    for warning in warnings:
        if warning not in deduped:
            deduped.append(warning)
    return deduped


def _next_action(warnings: list[str]) -> str:
    if any("AIRTABLE_API_KEY" in warning for warning in warnings):
        return "Add AIRTABLE_API_KEY to enable live Airtable writes from scheduled runs."
    if any("GOOGLE" in warning for warning in warnings):
        return "Add Google credentials only if live Google Docs links are required."
    return "Review generated Signals, Content Ideas, Sales Leads, and Weekly Report."
