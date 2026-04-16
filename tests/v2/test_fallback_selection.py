from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from pipelines.v2.analysis import evaluate_earthquake_feasibility, run_analysis


class FallbackSelectionTests(unittest.TestCase):
    def test_earthquake_feasibility_accepts_dense_series(self) -> None:
        monthly = pd.DataFrame(
            {
                "month": pd.date_range("2020-01-01", periods=30, freq="MS"),
                "earthquake_events": [1, 1, 2, 1, 0, 1, 1, 2, 1, 1, 1, 2, 1, 1, 2, 1, 0, 1, 1, 2, 1, 1, 1, 2, 1, 1, 2, 1, 1, 1],
            }
        )

        result = evaluate_earthquake_feasibility(
            monthly,
            feasibility_config={
                "min_total_months": 24,
                "min_nonzero_months": 12,
                "min_total_events": 18,
                "max_zero_share": 0.75,
                "max_consecutive_zero_months": 12,
            },
        )

        self.assertTrue(result.is_viable)

    def test_run_analysis_uses_pca_fallback_when_earthquakes_are_sparse(self) -> None:
        months = pd.date_range("2020-01-01", periods=30, freq="MS")
        monthly = pd.DataFrame(
            {
                "month": months,
                "total_events": np.linspace(5, 40, 30).round().astype(int),
                "unique_municipalities": np.linspace(2, 12, 30).round().astype(int),
                "earthquake_events": [0] * 14 + [1] + [0] * 15,
                "geophysical_events": [0] * 10 + [1, 0, 1, 0, 1] + [0] * 15,
                "hydrometeorological_events": np.linspace(2, 20, 30),
                "infrastructure_service_events": np.linspace(1, 8, 30),
                "technological_anthropogenic_events": np.linspace(0, 4, 30),
                "affected_families_total": np.linspace(5, 300, 30),
                "destroyed_houses_total": np.linspace(0, 25, 30),
                "damaged_houses_total": np.linspace(1, 40, 30),
                "destroyed_aqueducts_total": np.linspace(0, 5, 30),
                "affected_roads_total": np.linspace(1, 20, 30),
                "affected_bridges_total": np.linspace(0, 3, 30),
                "affected_educational_establishments_total": np.linspace(0, 4, 30),
                "affected_hectares_total": np.linspace(0, 150, 30),
                "injuries_total": np.linspace(0, 10, 30),
                "missing_persons_total": np.zeros(30),
                "deaths_total": np.linspace(0, 3, 30),
                "human_impact_total": np.linspace(0, 13, 30),
                "housing_impact_total": np.linspace(1, 65, 30),
                "infrastructure_impact_total": np.linspace(1, 32, 30),
            }
        )
        event_type_matrix = pd.DataFrame(
            {
                "month": months,
                "Floods": np.linspace(1, 15, 30).round().astype(int),
                "Forest fire": np.linspace(3, 12, 30).round().astype(int),
                "Earthquake": [0] * 14 + [1] + [0] * 15,
            }
        )
        municipality_summary = pd.DataFrame({"municipality_en": ["A", "B"], "event_count": [20, 18]})

        with tempfile.TemporaryDirectory() as temp_dir:
            analysis = run_analysis(
                classified=pd.DataFrame(),
                monthly=monthly,
                event_type_matrix=event_type_matrix,
                municipality_summary=municipality_summary,
                config={
                    "rolling_window_months": 6,
                    "stl_period": 12,
                    "shock_window_months": 6,
                    "pelt_penalty_multiplier": 2.5,
                    "feasibility": {
                        "min_total_months": 24,
                        "min_nonzero_months": 12,
                        "min_total_events": 18,
                        "max_zero_share": 0.75,
                        "max_consecutive_zero_months": 12,
                    },
                    "fallback": {
                        "pca_min_features": 3,
                        "pca_min_months": 18,
                        "entropy_min_event_types": 2,
                        "entropy_min_months_with_events": 12,
                        "candidate_features": [
                            "total_events",
                            "unique_municipalities",
                            "earthquake_events",
                            "geophysical_events",
                            "hydrometeorological_events",
                            "infrastructure_service_events",
                            "technological_anthropogenic_events",
                            "affected_families_total",
                            "destroyed_houses_total",
                            "damaged_houses_total",
                        ],
                    },
                },
                figures_dir=Path(temp_dir),
            )

        self.assertEqual(analysis["branch"], "pca_index")
        self.assertTrue(analysis["selected_features"])
        self.assertFalse(analysis["pca_loadings"].empty)


if __name__ == "__main__":
    unittest.main()
