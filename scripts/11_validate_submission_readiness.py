#!/usr/bin/env python
"""Validate whether the repository is ready for an empirical NeurIPS submission."""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from privatemap.io.config import load_experiment_config, load_yaml, resolve_repo_path


@dataclass(frozen=True)
class Check:
    level: str
    name: str
    message: str
    strict_fail: bool = False


def _csv_has_rows(path: Path) -> bool:
    if not path.exists():
        return False
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return False
        return any(True for _ in reader)


def _non_gitkeep_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted(item for item in path.iterdir() if item.is_file() and item.name != ".gitkeep")


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _status(condition: bool, *, name: str, ok: str, warn: str, strict_fail: bool) -> Check:
    if condition:
        return Check("PASS", name, ok)
    return Check("WARN", name, warn, strict_fail=strict_fail)


def collect_checks(config_path: str | Path) -> list[Check]:
    config = load_experiment_config(config_path)
    paths = load_yaml(config["paths_config"])
    paper_cfg = load_yaml(config["paper_config"])["paper"]

    results_dir = resolve_repo_path(paths["results_dir"])
    figures_dir = resolve_repo_path(paths["figures_dir"])
    tables_dir = resolve_repo_path(paths["tables_dir"])
    paper_path = resolve_repo_path(paper_cfg["tex_path"])
    checklist_path = resolve_repo_path(paper_cfg["checklist_path"])
    style_path = resolve_repo_path("paper/neurips_2026.sty")

    privacy_results = results_dir / "privacy_results.csv"
    utility_results = results_dir / "utility_results.csv"
    aggregate_csv = results_dir / "aggregated_results.csv"
    aggregate_json = results_dir / "aggregated_results.json"

    checks = [
        _status(
            _csv_has_rows(privacy_results),
            name="privacy results",
            ok=f"{privacy_results} exists and has rows",
            warn=f"{privacy_results} is missing or empty",
            strict_fail=True,
        ),
        _status(
            _csv_has_rows(utility_results),
            name="utility results",
            ok=f"{utility_results} exists and has rows",
            warn=f"{utility_results} is missing or empty",
            strict_fail=True,
        ),
        _status(
            aggregate_csv.exists() or aggregate_json.exists(),
            name="aggregate summaries",
            ok="aggregate summary file exists",
            warn="aggregate summary file is missing",
            strict_fail=True,
        ),
        _status(
            bool(_non_gitkeep_files(tables_dir)),
            name="paper tables",
            ok=f"generated table files found in {tables_dir}",
            warn=f"no generated table files found in {tables_dir}",
            strict_fail=True,
        ),
        _status(
            bool(_non_gitkeep_files(figures_dir)),
            name="paper figures",
            ok=f"generated figure files found in {figures_dir}",
            warn=f"no generated figure files found in {figures_dir}",
            strict_fail=True,
        ),
        _status(
            style_path.exists(),
            name="NeurIPS style",
            ok=f"{style_path} exists",
            warn=f"{style_path} is missing; copy the official NeurIPS 2026 style file",
            strict_fail=True,
        ),
    ]

    checklist_text = _read_text(checklist_path).lower()
    checklist_has_placeholder = any(
        marker in checklist_text for marker in ["todo", "tbd", "placeholder", "replace"]
    )
    checks.append(
        _status(
            not checklist_has_placeholder,
            name="official checklist",
            ok="checklist does not contain obvious placeholders",
            warn=f"{checklist_path} still appears to contain placeholder language",
            strict_fail=True,
        )
    )

    paper_text = _read_text(paper_path)
    lower_paper = paper_text.lower()
    checks.extend(
        [
            _status(
                "tbd" not in lower_paper,
                name="paper TBD markers",
                ok="paper contains no TBD markers",
                warn=f"{paper_path} still contains TBD markers",
                strict_fail=True,
            ),
            _status(
                "does not report completed experimental results" not in lower_paper
                and "pre-experiment draft" not in lower_paper,
                name="draft no-results language",
                ok="paper no longer contains draft no-results language",
                warn="paper still says results are not completed; expected before experiments",
                strict_fail=True,
            ),
        ]
    )

    runs = config["experiment"].get("runs", [])
    checks.append(
        _status(
            bool(runs),
            name="configured runs",
            ok=f"{len(runs)} run(s) configured",
            warn="no real runs configured in experiment config",
            strict_fail=True,
        )
    )
    return checks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiment.yaml")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    checks = collect_checks(args.config)
    for check in checks:
        print(f"{check.level}: {check.name}: {check.message}")

    if args.strict:
        failures = [check for check in checks if check.strict_fail and check.level != "PASS"]
        if failures:
            print(f"FAIL: {len(failures)} strict submission requirement(s) are not met.")
            raise SystemExit(1)
    print("PASS: validation completed without fabricating missing data.")


if __name__ == "__main__":
    main()
