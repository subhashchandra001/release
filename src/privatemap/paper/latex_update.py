"""Minimal LaTeX helper utilities."""

from __future__ import annotations

from pathlib import Path


def replace_marker(tex_path: str | Path, marker: str, replacement: str) -> None:
    path = Path(tex_path)
    if not path.exists():
        raise FileNotFoundError(f"LaTeX file does not exist: {path}")
    text = path.read_text(encoding="utf-8")
    if marker not in text:
        raise ValueError(f"Marker not found in LaTeX file {path}: {marker}")
    path.write_text(text.replace(marker, replacement), encoding="utf-8")
