from __future__ import annotations

import unittest

import pandas as pd

from pipelines.v2.classification import detect_earthquake_events


class EarthquakeDetectionTests(unittest.TestCase):
    def test_earthquake_detection_scans_multiple_fields(self) -> None:
        dataframe = pd.DataFrame(
            {
                "event_type_es": ["INUNDACIONES", "SISMO", "CIERRE DE VIA"],
                "probable_cause_es": ["FUERTES LLUVIAS", "INDETERMINADO", "INDETERMINADO"],
                "observations_es": [
                    "Se reporta movimiento sísmico leve sin daños.",
                    "Normalidad posterior al evento.",
                    "El temblor generó revisión preventiva de la vía.",
                ],
            }
        )

        detected = detect_earthquake_events(
            dataframe,
            search_fields=["event_type_es", "probable_cause_es", "observations_es"],
            earthquake_terms=["sismo", "terremoto", "temblor", "movimiento sísmico", "movimiento sismico"],
        )

        self.assertEqual(detected["earthquake_detected"].tolist(), [True, True, True])
        self.assertIn("event_type", detected.loc[1, "earthquake_detection_sources"])
        self.assertIn("observations", detected.loc[0, "earthquake_detection_sources"])


if __name__ == "__main__":
    unittest.main()
