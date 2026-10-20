from __future__ import annotations

from html import escape
from pathlib import Path

from .models import ScanResult


def write_reports(result: ScanResult, report_dir: Path) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = result.started_at.strftime("%Y%m%d-%H%M%S")
    html_path = report_dir / f"storage-health-{stamp}.html"
    text_path = report_dir / f"storage-health-{stamp}.txt"
    html_path.write_text(render_html(result), encoding="utf-8")
    text_path.write_text(render_text(result), encoding="utf-8")
    return html_path, text_path


def render_html(result: ScanResult) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Storage Health Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #1f2937; }}
    h1, h2 {{ color: #111827; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 24px; }}
    th, td {{ border: 1px solid #d1d5db; padding: 8px; text-align: left; }}
    th {{ background: #f3f4f6; }}
    .ok {{ color: #047857; }}
    .warning {{ color: #b45309; }}
    .critical {{ color: #b91c1c; font-weight: bold; }}
  </style>
</head>
<body>
  <h1>Storage Health Report</h1>
  <p>Started: {escape(result.started_at.isoformat(sep=" ", timespec="seconds"))}<br>
  Ended: {escape(result.ended_at.isoformat(sep=" ", timespec="seconds"))}</p>

  <h2>Partition Statistics</h2>
  <table>
    <tr><th>Name</th><th>Total GB</th><th>Used GB</th><th>Free GB</th><th>Usage</th><th>Status</th></tr>
    {''.join(_partition_row(partition) for partition in result.partitions)}
  </table>

  <h2>Alerts</h2>
  {_list(result.alerts)}

  <h2>Recommendations</h2>
  {_list(result.recommendations)}

  <h2>Largest Files</h2>
  <table>
    <tr><th>Name</th><th>Path</th><th>Size GB</th><th>Modified</th></tr>
    {''.join(_file_row(file) for file in result.large_files)}
  </table>

  <h2>Largest Folders</h2>
  <table>
    <tr><th>Path</th><th>Size GB</th></tr>
    {''.join(_folder_row(folder) for folder in result.large_folders)}
  </table>
</body>
</html>
"""


def render_text(result: ScanResult) -> str:
    lines = [
        "Storage Health Report",
        f"Started: {result.started_at.isoformat(sep=' ', timespec='seconds')}",
        f"Ended: {result.ended_at.isoformat(sep=' ', timespec='seconds')}",
        "",
        "Partitions:",
    ]
    for partition in result.partitions:
        lines.append(
            f"- {partition.name}: {partition.used_gb}/{partition.total_gb} GB used "
            f"({partition.usage_percent}%, {partition.status})"
        )
    lines.extend(["", "Alerts:"])
    lines.extend(f"- {alert}" for alert in result.alerts or ["None"])
    lines.extend(["", "Recommendations:"])
    lines.extend(f"- {item}" for item in result.recommendations)
    lines.extend(["", "Largest Files:"])
    lines.extend(f"- {file.size_gb} GB | {file.modified_date.date()} | {file.path}" for file in result.large_files)
    lines.extend(["", "Largest Folders:"])
    lines.extend(f"- {folder.size_gb} GB | {folder.path}" for folder in result.large_folders)
    return "\n".join(lines) + "\n"


def _partition_row(partition) -> str:
    return (
        "<tr>"
        f"<td>{escape(partition.name)}</td>"
        f"<td>{partition.total_gb}</td>"
        f"<td>{partition.used_gb}</td>"
        f"<td>{partition.free_gb}</td>"
        f"<td>{partition.usage_percent}%</td>"
        f"<td class=\"{escape(partition.status)}\">{escape(partition.status)}</td>"
        "</tr>"
    )


def _file_row(file) -> str:
    return (
        "<tr>"
        f"<td>{escape(file.name)}</td>"
        f"<td>{escape(str(file.path))}</td>"
        f"<td>{file.size_gb}</td>"
        f"<td>{escape(file.modified_date.date().isoformat())}</td>"
        "</tr>"
    )


def _folder_row(folder) -> str:
    return f"<tr><td>{escape(str(folder.path))}</td><td>{folder.size_gb}</td></tr>"


def _list(items: list[str]) -> str:
    if not items:
        return "<p>None</p>"
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"
