"""Paper table generation from actual benchmark result files."""

from __future__ import annotations

from pathlib import Path

from privatemap.io.results_io import (
    ResultsIOError,
    aggregate_results,
    read_privacy_results,
    read_utility_results,
)


def aggregate_result_files(paths: list[str | Path], *, kind: str) -> list[dict]:
    if not paths:
        raise ResultsIOError("No result files were provided")
    reader = read_privacy_results if kind == "privacy" else read_utility_results
    return aggregate_results([reader(path) for path in paths])


def records_to_markdown(records: list[dict]) -> str:
    if not records:
        raise ResultsIOError("No records available for table generation")
    columns = list(records[0])
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for record in records:
        row = [_format(record.get(column, "")) for column in columns]
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def records_to_latex_tabular(records: list[dict]) -> str:
    if not records:
        raise ResultsIOError("No records available for table generation")
    columns = list(records[0])
    lines = [
        "\\begin{tabular}{" + "l" * len(columns) + "}",
        " & ".join(columns) + " \\\\",
        "\\hline",
    ]
    for record in records:
        lines.append(" & ".join(_format(record.get(column, "")) for column in columns) + " \\\\")
    lines.append("\\end{tabular}")
    return "\n".join(lines) + "\n"


def write_table(records: list[dict], path: str | Path, *, fmt: str = "markdown") -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = records_to_latex_tabular(records) if fmt == "latex" else records_to_markdown(records)
    destination.write_text(text, encoding="utf-8")


def _format(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)
