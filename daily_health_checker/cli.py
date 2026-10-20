from __future__ import annotations

from argparse import ArgumentParser
from datetime import datetime
import logging

from .analyzer import build_alerts, build_recommendations
from .config import load_config
from .logger import configure_logging
from .models import ScanResult
from .notifier import send_report
from .reporter import write_reports
from .scanner import discover_partitions, scan_directories


def main() -> int:
    parser = ArgumentParser(description="Daily System & Storage Health Checker")
    parser.add_argument("--config", required=True, help="Path to JSON configuration file.")
    args = parser.parse_args()

    config = load_config(args.config)
    log_path = configure_logging(config.log_dir)
    logging.info("Storage health scan started.")

    started_at = datetime.now()
    try:
        partitions = discover_partitions(config.warning_threshold_percent, config.critical_threshold_percent)
        large_files, large_folders = scan_directories(config.scan_directories, config.top_n)
        alerts = build_alerts(partitions)
        recommendations = build_recommendations(large_files, large_folders, config.old_file_days)
        ended_at = datetime.now()
        result = ScanResult(partitions, large_files, large_folders, alerts, recommendations, started_at, ended_at)
        html_report, text_report = write_reports(result, config.report_dir)
        logging.info("Reports generated: %s and %s", html_report, text_report)

        if config.email.enabled:
            send_report(config.email, html_report)
            logging.info("Email report sent to %s", config.email.recipient)

        logging.info("Storage health scan completed. Log: %s", log_path)
        print(f"HTML report: {html_report}")
        print(f"Text report: {text_report}")
        return 0
    except Exception:
        logging.exception("Storage health scan failed.")
        return 1
