from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass(frozen=True)
class EmailConfig:
    enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    username: str = ""
    password_env: str = "STORAGE_HEALTH_EMAIL_PASSWORD"
    recipient: str = ""
    sender: str = ""


@dataclass(frozen=True)
class AppConfig:
    scan_directories: list[Path] = field(default_factory=lambda: [Path.home()])
    report_dir: Path = Path("./reports")
    log_dir: Path = Path("./logs")
    top_n: int = 20
    warning_threshold_percent: float = 80.0
    critical_threshold_percent: float = 90.0
    old_file_days: int = 180
    email: EmailConfig = field(default_factory=EmailConfig)


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path).expanduser().resolve()
    data = json.loads(config_path.read_text(encoding="utf-8"))
    base_dir = config_path.parent

    def resolve_path(value: str) -> Path:
        expanded = Path(value).expanduser()
        if expanded.is_absolute():
            return expanded
        return (base_dir / expanded).resolve()

    email_data = data.get("email", {})
    return AppConfig(
        scan_directories=[resolve_path(item) for item in data.get("scan_directories", ["~"])],
        report_dir=resolve_path(data.get("report_dir", "./reports")),
        log_dir=resolve_path(data.get("log_dir", "./logs")),
        top_n=int(data.get("top_n", 20)),
        warning_threshold_percent=float(data.get("warning_threshold_percent", 80)),
        critical_threshold_percent=float(data.get("critical_threshold_percent", 90)),
        old_file_days=int(data.get("old_file_days", 180)),
        email=EmailConfig(
            enabled=bool(email_data.get("enabled", False)),
            smtp_host=str(email_data.get("smtp_host", "")),
            smtp_port=int(email_data.get("smtp_port", 587)),
            username=str(email_data.get("username", "")),
            password_env=str(email_data.get("password_env", "STORAGE_HEALTH_EMAIL_PASSWORD")),
            recipient=str(email_data.get("recipient", "")),
            sender=str(email_data.get("sender", "")),
        ),
    )
