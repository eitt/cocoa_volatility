from __future__ import annotations

import unittest

import pandas as pd

from pipelines.v2.aggregation import aggregate_monthly_events


class AggregationTests(unittest.TestCase):
    def test_monthly_aggregation_preserves_counts_and_domains(self) -> None:
        dataframe = pd.DataFrame(
            {
                "event_id": ["EVT00001", "EVT00002", "EVT00003"],
                "month": pd.to_datetime(["2020-01-01", "2020-01-01", "2020-02-01"]),
                "municipality_en": ["Bucaramanga", "Bucaramanga", "Piedecuesta"],
                "earthquake_detected": [True, False, False],
                "hazard_domain_key": ["geophysical", "hydrometeorological", "infrastructure_service"],
                "event_type_en": ["Earthquake", "Floods", "Road closure"],
                "affected_families": [1.0, 2.0, 0.0],
                "destroyed_houses": [0.0, 1.0, 0.0],
                "damaged_houses": [0.0, 0.0, 0.0],
                "destroyed_aqueducts": [0.0, 0.0, 0.0],
                "affected_roads": [0.0, 0.0, 1.0],
                "affected_bridges": [0.0, 0.0, 0.0],
                "affected_educational_establishments": [0.0, 0.0, 0.0],
                "affected_hectares": [0.0, 3.0, 0.0],
                "injuries": [0.0, 0.0, 0.0],
                "missing_persons": [0.0, 0.0, 0.0],
                "deaths": [0.0, 0.0, 0.0],
                "human_impact_total": [0.0, 0.0, 0.0],
                "housing_impact_total": [0.0, 1.0, 0.0],
                "infrastructure_impact_total": [0.0, 0.0, 1.0],
            }
        )

        monthly, event_type_matrix = aggregate_monthly_events(dataframe)

        january = monthly.loc[monthly["month"] == pd.Timestamp("2020-01-01")].iloc[0]
        february = monthly.loc[monthly["month"] == pd.Timestamp("2020-02-01")].iloc[0]

        self.assertEqual(january["total_events"], 2)
        self.assertEqual(january["earthquake_events"], 1)
        self.assertEqual(january["geophysical_events"], 1)
        self.assertEqual(january["hydrometeorological_events"], 1)
        self.assertEqual(february["infrastructure_service_events"], 1)
        self.assertIn("Earthquake", event_type_matrix.columns)
        self.assertIn("Road closure", event_type_matrix.columns)


if __name__ == "__main__":
    unittest.main()
