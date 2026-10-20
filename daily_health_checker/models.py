from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class PartitionRecord:
    name: str
    total_gb: float
    used_gb: float
    free_gb: float
    usage_percent: float
    status: str


@dataclass(frozen=True)
class FileRecord:
    name: str
    path: Path
    size_gb: float
    modified_date: datetime


@dataclass(frozen=True)
class FolderRecord:
    path: Path
    size_gb: float


@dataclass(frozen=True)
class ScanResult:
    partitions: list[PartitionRecord]
    large_files: list[FileRecord]
    large_folders: list[FolderRecord]
    alerts: list[str]
    recommendations: list[str]
    started_at: datetime
    ended_at: datetime
