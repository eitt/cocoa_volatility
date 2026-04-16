from __future__ import annotations

from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from pipelines.v2.reporting import build_markdown_report, render_pandoc_outputs


def _sample_tables() -> dict[str, pd.DataFrame]:
    return {
        "dataset_overview": pd.DataFrame(
            [
                {"metric": "Source rows", "value": 10},
                {"metric": "Months in observation window", "value": 12},
                {"metric": "Date range start", "value": "2020-01-01"},
                {"metric": "Date range end", "value": "2020-12-01"},
                {"metric": "Distinct municipalities", "value": 2},
                {"metric": "Distinct event types", "value": 3},
                {"metric": "Earthquake-related events", "value": 1},
            ]
        ),
        "event_type_summary": pd.DataFrame(
            [
                {"event_type_en": "Floods", "event_count": 5, "deaths_total": 0, "injuries_total": 0, "affected_families_total": 10, "share_pct": 50.0}
            ]
        ),
        "municipality_summary": pd.DataFrame(
            [
                {"municipality_en": "Bucaramanga", "event_count": 4, "unique_event_types": 2, "deaths_total": 0, "affected_families_total": 8}
            ]
        ),
        "translation_strategy_summary": pd.DataFrame(
            [
                {"context": "event_type", "translation_strategy": "exact_dictionary_match", "value_count": 3}
            ]
        ),
    }


class ReportGenerationTests(unittest.TestCase):
    def _sample_analysis(self, tmp_path: Path) -> dict[str, object]:
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()
        for name in ["a.png", "b.png", "c.png", "d.png", "e.png", "f.png", "g.png"]:
            (figures_dir / name).write_bytes(b"")

        return {
            "branch": "pca_index",
            "branch_label": "PCA-based crisis indicator",
            "branch_reason": "The earthquake series is too sparse, so v2 switches to the first valid fallback: a PCA-based monthly crisis indicator.",
            "feasibility": {
                "total_months": 12,
                "nonzero_months": 1,
                "total_events": 1,
                "zero_share": 0.91,
                "max_consecutive_zero_months": 8,
                "is_viable": False,
            },
            "feasibility_table": pd.DataFrame(
                [{"criterion": "Total months", "observed_value": 12, "threshold": 24, "rule": ">=", "passes": False}]
            ),
            "common_figures": {
                "monthly_totals": str(figures_dir / "a.png"),
                "hazard_mix": str(figures_dir / "b.png"),
                "municipalities": str(figures_dir / "c.png"),
            },
            "branch_figures": {
                "rolling": str(figures_dir / "d.png"),
                "change_points": str(figures_dir / "e.png"),
                "decomposition": str(figures_dir / "f.png"),
                "pca_loadings": str(figures_dir / "g.png"),
            },
            "branch_tables": {
                "structural_comparison": pd.DataFrame(
                    [{"comparison": "Mean shift (Welch t-test)", "before_value": 1.0, "after_value": 2.0, "statistic": 0.5, "p_value": 0.6}]
                ),
                "pca_loadings": pd.DataFrame([{"feature": "total_events", "loading": 0.7}]),
            },
            "branch_summary": {"mean": 0.1, "std": 0.5, "coefficient_of_variation": 5.0},
            "change_dates": ["2020-03-01"],
            "shock_date": "2020-03-01",
            "selected_features": ["total_events", "affected_families_total"],
            "explained_variance_ratio": 0.45,
        }

    def test_build_markdown_report_contains_required_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            content = build_markdown_report(
                markdown_path=tmp_path / "report.md",
                config={"report": {"title": "T", "author": "A", "keywords": ["one", "two"]}},
                input_file=Path("input.csv"),
                analysis=self._sample_analysis(tmp_path),
                tables=_sample_tables(),
            )

        for section in [
            "# Introduction",
            "# Literature-Style Framing",
            "# Data and Methods",
            "# Results",
            "# Discussion",
            "# Limitations",
        ]:
            self.assertIn(section, content)

    def test_render_pandoc_outputs_invokes_docx_and_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            markdown_path = tmp_path / "report.md"
            markdown_path.write_text("# Report\n", encoding="utf-8")

            calls: list[list[str]] = []

            def fake_run(command: list[str], cwd: Path, check: bool) -> subprocess.CompletedProcess[str]:
                calls.append(command)
                return subprocess.CompletedProcess(command, 0)

            with patch("pipelines.v2.reporting.subprocess.run", side_effect=fake_run):
                outputs = render_pandoc_outputs(markdown_path, tmp_path / "report.docx", tmp_path / "report.pdf")

        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0][0], "pandoc")
        self.assertIn("--pdf-engine=pdflatex", calls[1])
        self.assertTrue(outputs["docx"].endswith("report.docx"))
        self.assertTrue(outputs["pdf"].endswith("report.pdf"))


if __name__ == "__main__":
    unittest.main()
