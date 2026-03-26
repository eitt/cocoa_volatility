"""Helpers for transparent missing-value imputation in aligned panels."""

from __future__ import annotations

import pandas as pd
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer, KNNImputer


def run_knn_imputation(
    dataframe: pd.DataFrame,
    value_columns: list[str],
    n_neighbors: int = 5,
) -> pd.DataFrame:
    """Impute missing numeric values with KNN."""
    imputed = dataframe.copy()
    effective_neighbors = max(1, min(n_neighbors, max(1, len(imputed) - 1)))
    model = KNNImputer(n_neighbors=effective_neighbors)
    imputed[value_columns] = model.fit_transform(imputed[value_columns])
    return imputed


def run_iterative_imputation(
    dataframe: pd.DataFrame,
    value_columns: list[str],
    random_state: int = 42,
    max_iter: int = 50,
) -> pd.DataFrame:
    """Impute missing numeric values with multivariate iterative imputation."""
    imputed = dataframe.copy()
    model = IterativeImputer(random_state=random_state, max_iter=max_iter, sample_posterior=False)
    imputed[value_columns] = model.fit_transform(imputed[value_columns])
    return imputed


def add_imputation_flags(
    original: pd.DataFrame,
    imputed: pd.DataFrame,
    value_columns: list[str],
) -> pd.DataFrame:
    """Append boolean flags showing which cells were imputed."""
    flagged = imputed.copy()
    for column in value_columns:
        flagged[f"imputed_{column}"] = original[column].isna() & flagged[column].notna()
    return flagged


def build_imputation_audit(
    original: pd.DataFrame,
    value_columns: list[str],
    date_column: str,
    method_frames: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """Summarize each missing cell and its candidate imputed values."""
    records: list[dict[str, object]] = []

    for row_index, row in original.iterrows():
        for column in value_columns:
            if pd.notna(row[column]):
                continue

            record = {
                "date": row[date_column],
                "variable": column,
                "original_value": None,
            }
            for method_name, frame in method_frames.items():
                record[f"{method_name}_imputed_value"] = frame.loc[row_index, column]
            records.append(record)

    return pd.DataFrame.from_records(records)
