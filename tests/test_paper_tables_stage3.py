from __future__ import annotations

from privatemap.paper.tables import records_to_latex_tabular, records_to_markdown, write_table


def test_paper_table_generation_from_records(tmp_path) -> None:
    records = [{"metric_name": "iou", "mean": 0.5, "count": 2}]
    markdown = records_to_markdown(records)
    latex = records_to_latex_tabular(records)
    assert "metric_name" in markdown
    assert "\\begin{tabular}" in latex
    path = tmp_path / "table.md"
    write_table(records, path)
    assert path.read_text(encoding="utf-8").startswith("|")
