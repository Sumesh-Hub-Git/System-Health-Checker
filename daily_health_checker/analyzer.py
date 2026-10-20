from __future__ import annotations

from datetime import datetime, timedelta

from .models import FileRecord, FolderRecord, PartitionRecord


def build_alerts(partitions: list[PartitionRecord]) -> list[str]:
    alerts = []
    for partition in partitions:
        if partition.status == "critical":
            alerts.append(f"Critical disk usage on {partition.name}: {partition.usage_percent}% used.")
        elif partition.status == "warning":
            alerts.append(f"Warning disk usage on {partition.name}: {partition.usage_percent}% used.")
    return alerts


def build_recommendations(
    large_files: list[FileRecord],
    large_folders: list[FolderRecord],
    old_file_days: int,
    now: datetime | None = None,
) -> list[str]:
    now = now or datetime.now()
    recommendations: list[str] = []

    for folder in large_folders[:5]:
        if folder.size_gb >= 1:
            recommendations.append(f"Review large folder: {folder.path} ({folder.size_gb} GB).")

    old_cutoff = now - timedelta(days=old_file_days)
    old_large_files = [file for file in large_files if file.modified_date < old_cutoff and file.size_gb >= 1]
    for file in old_large_files[:5]:
        recommendations.append(f"Review old large file: {file.path} ({file.size_gb} GB).")

    downloads = [folder for folder in large_folders if "downloads" in str(folder.path).lower()]
    if downloads:
        folder = downloads[0]
        recommendations.append(f"Review Downloads folder: {folder.path} ({folder.size_gb} GB).")

    if not recommendations:
        recommendations.append("No immediate cleanup recommendations found.")

    return recommendations
