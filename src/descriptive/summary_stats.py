"""Descriptive statistics helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_summary_statistics(dataframe: pd.DataFrame, value_columns: list[str]) -> pd.DataFrame:
    """Return count, mean, dispersion, and quantiles for selected columns."""
    available = [column for column in value_columns if column in dataframe.columns]
    if not available:
        return pd.DataFrame()
    numeric = dataframe[available].apply(pd.to_numeric, errors="coerce")
    summary = numeric.describe().transpose()
    summary.index.name = "variable"
    return summary.reset_index()


def compute_extended_summary_statistics(dataframe: pd.DataFrame, value_columns: list[str]) -> pd.DataFrame:
    """Return descriptive statistics with shape and dispersion diagnostics."""
    available = [column for column in value_columns if column in dataframe.columns]
    if not available:
        return pd.DataFrame()

    numeric = dataframe[available].apply(pd.to_numeric, errors="coerce")
    summary = numeric.describe().transpose()
    summary["missing_observations"] = numeric.isna().sum()
    summary["skewness"] = numeric.skew()
    summary["kurtosis"] = numeric.kurtosis()
    summary["iqr"] = summary["75%"] - summary["25%"]
    summary["coefficient_of_variation"] = np.where(
        summary["mean"].abs() > 0,
        summary["std"] / summary["mean"].abs(),
        np.nan,
    )
    summary.index.name = "variable"
    return summary.reset_index()


def compute_series_coverage(dataframe: pd.DataFrame, date_column: str, value_columns: list[str]) -> pd.DataFrame:
    """Summarize non-missing coverage and observation windows for selected series."""
    available = [column for column in value_columns if column in dataframe.columns]
    if date_column not in dataframe.columns or not available:
        return pd.DataFrame()

    frame = dataframe[[date_column] + available].copy()
    frame[date_column] = pd.to_datetime(frame[date_column], errors="coerce")
    total_rows = len(frame)

    records: list[dict[str, object]] = []
    for column in available:
        observed = frame.loc[frame[column].notna(), date_column]
        first_observation = observed.min() if not observed.empty else pd.NaT
        last_observation = observed.max() if not observed.empty else pd.NaT
        span_months = None
        if pd.notna(first_observation) and pd.notna(last_observation):
            span_months = (
                (last_observation.year - first_observation.year) * 12
                + last_observation.month
                - first_observation.month
                + 1
            )

        non_missing = int(frame[column].notna().sum())
        records.append(
            {
                "variable": column,
                "non_missing_observations": non_missing,
                "missing_observations": int(total_rows - non_missing),
                "coverage_share": non_missing / total_rows if total_rows else None,
                "first_observation": first_observation.date().isoformat() if pd.notna(first_observation) else None,
                "last_observation": last_observation.date().isoformat() if pd.notna(last_observation) else None,
                "span_months": span_months,
            }
        )

    return pd.DataFrame.from_records(records)


def compute_pairwise_overlap_matrix(dataframe: pd.DataFrame, value_columns: list[str]) -> pd.DataFrame:
    """Count pairwise non-missing overlaps for the selected series."""
    available = [column for column in value_columns if column in dataframe.columns]
    if not available:
        return pd.DataFrame()

    overlap = pd.DataFrame(index=available, columns=available, dtype="Int64")
    for row_column in available:
        for column_column in available:
            overlap.loc[row_column, column_column] = int(
                dataframe[[row_column, column_column]].dropna().shape[0]
            )
    return overlap


def compute_correlation_matrix(
    dataframe: pd.DataFrame,
    value_columns: list[str],
    method: str = "pearson",
) -> pd.DataFrame:
    """Compute a correlation matrix for the selected numeric series."""
    available = [column for column in value_columns if column in dataframe.columns]
    if not available:
        return pd.DataFrame()

    numeric = dataframe[available].apply(pd.to_numeric, errors="coerce")
    return numeric.corr(method=method)
