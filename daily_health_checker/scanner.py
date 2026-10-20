from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from heapq import nlargest
from pathlib import Path
import logging
import os
import shutil
import sys

from .models import FileRecord, FolderRecord, PartitionRecord


BYTES_PER_GB = 1024 ** 3


def discover_partitions(warning_threshold: float, critical_threshold: float) -> list[PartitionRecord]:
    roots = _candidate_roots()
    records: list[PartitionRecord] = []
    seen: set[str] = set()

    for root in roots:
        try:
            usage = shutil.disk_usage(root)
        except OSError as exc:
            logging.warning("Unable to read disk usage for %s: %s", root, exc)
            continue

        key = str(Path(root).resolve())
        if key in seen:
            continue
        seen.add(key)

        used = usage.total - usage.free
        usage_percent = (used / usage.total * 100) if usage.total else 0.0
        status = "critical" if usage_percent >= critical_threshold else "warning" if usage_percent >= warning_threshold else "ok"
        records.append(
            PartitionRecord(
                name=str(root),
                total_gb=round(usage.total / BYTES_PER_GB, 2),
                used_gb=round(used / BYTES_PER_GB, 2),
                free_gb=round(usage.free / BYTES_PER_GB, 2),
                usage_percent=round(usage_percent, 1),
                status=status,
            )
        )

    return records


def scan_directories(scan_dirs: list[Path], top_n: int) -> tuple[list[FileRecord], list[FolderRecord]]:
    file_entries: list[tuple[int, Path, datetime]] = []
    folder_sizes: defaultdict[Path, int] = defaultdict(int)

    for root in scan_dirs:
        if not root.exists():
            logging.warning("Scan directory does not exist: %s", root)
            continue
        for current_dir, dirnames, filenames in os.walk(root, topdown=True, onerror=_log_walk_error):
            current_path = Path(current_dir)
            _prune_inaccessible_dirs(current_path, dirnames)
            for filename in filenames:
                path = current_path / filename
                try:
                    stat = path.stat()
                except OSError as exc:
                    logging.warning("Unable to stat file %s: %s", path, exc)
                    continue
                size = stat.st_size
                modified = datetime.fromtimestamp(stat.st_mtime)
                file_entries.append((size, path, modified))
                _add_size_to_parent_folders(folder_sizes, root, path.parent, size)

    largest_files = [
        FileRecord(path.name, path, round(size / BYTES_PER_GB, 3), modified)
        for size, path, modified in nlargest(top_n, file_entries, key=lambda item: item[0])
    ]
    largest_folders = [
        FolderRecord(path, round(size / BYTES_PER_GB, 3))
        for path, size in nlargest(top_n, folder_sizes.items(), key=lambda item: item[1])
    ]
    return largest_files, largest_folders


def _candidate_roots() -> list[Path]:
    if sys.platform.startswith("win"):
        roots = []
        for code in range(ord("A"), ord("Z") + 1):
            drive = Path(f"{chr(code)}:/")
            if drive.exists():
                roots.append(drive)
        return roots or [Path.cwd().anchor]
    return [Path("/")]


def _add_size_to_parent_folders(folder_sizes: defaultdict[Path, int], scan_root: Path, folder: Path, size: int) -> None:
    scan_root = scan_root.resolve()
    folder = folder.resolve()
    while True:
        folder_sizes[folder] += size
        if folder == scan_root or folder.parent == folder:
            break
        folder = folder.parent


def _prune_inaccessible_dirs(current_path: Path, dirnames: list[str]) -> None:
    kept = []
    for dirname in dirnames:
        path = current_path / dirname
        try:
            path.stat()
        except OSError as exc:
            logging.warning("Skipping inaccessible directory %s: %s", path, exc)
            continue
        kept.append(dirname)
    dirnames[:] = kept


def _log_walk_error(error: OSError) -> None:
    logging.warning("Directory scan error: %s", error)
