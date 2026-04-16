from __future__ import annotations

from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from src.econometrics.stationarity_tests import run_stationarity_suite
from src.utils.file_utils import load_yaml


ROOT = Path(__file__).resolve().parents[2]


class V1NonRegressionTests(unittest.TestCase):
    def test_v1_core_files_remain_present(self) -> None:
        self.assertTrue((ROOT / "scripts" / "06_descriptive_analysis.py").exists())
        self.assertTrue((ROOT / "scripts" / "11_export_results.py").exists())
        self.assertTrue((ROOT / "paper" / "build_manuscript.ps1").exists())

    def test_v1_paths_config_is_unchanged_for_core_keys(self) -> None:
        paths = load_yaml(ROOT / "config" / "paths.yaml")

        self.assertEqual(paths["output_tables"], "outputs/tables")
        self.assertEqual(paths["output_figures"], "outputs/figures")
        self.assertEqual(paths["data_processed_analysis_ready"], "data/processed/analysis_ready")

    def test_v1_stationarity_helper_still_runs(self) -> None:
        dataframe = pd.DataFrame({"series": np.random.default_rng(7).normal(size=80)})

        results = run_stationarity_suite(dataframe, ["series"])

        self.assertFalse(results.empty)
        self.assertTrue(set(results["test"]) >= {"adf", "kpss", "pp"})


if __name__ == "__main__":
    unittest.main()
