from datetime import datetime, timedelta
from pathlib import Path

from daily_health_checker.analyzer import build_alerts, build_recommendations
from daily_health_checker.models import FileRecord, FolderRecord, PartitionRecord


def test_build_alerts_reports_warning_and_critical():
    partitions = [
        PartitionRecord("C:/", 100, 50, 50, 50, "ok"),
        PartitionRecord("D:/", 100, 81, 19, 81, "warning"),
        PartitionRecord("E:/", 100, 95, 5, 95, "critical"),
    ]

    alerts = build_alerts(partitions)

    assert alerts == [
        "Warning disk usage on D:/: 81% used.",
        "Critical disk usage on E:/: 95% used.",
    ]


def test_build_recommendations_flags_large_old_files_and_downloads():
    now = datetime(2026, 6, 2)
    files = [
        FileRecord("archive.zip", Path("C:/Users/A/Downloads/archive.zip"), 2.5, now - timedelta(days=365)),
    ]
    folders = [
        FolderRecord(Path("C:/Users/A/Downloads"), 12),
    ]

    recommendations = build_recommendations(files, folders, 180, now=now)

    assert "Review large folder: C:\\Users\\A\\Downloads (12 GB)." in recommendations
    assert "Review old large file: C:\\Users\\A\\Downloads\\archive.zip (2.5 GB)." in recommendations
    assert "Review Downloads folder: C:\\Users\\A\\Downloads (12 GB)." in recommendations
