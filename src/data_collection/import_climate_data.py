"""Import helpers for NASA POWER climate series."""

from __future__ import annotations

import pandas as pd

from src.data_collection.load_local_files import load_tabular_file


def load_nasa_power_series(file_path: str, **kwargs) -> pd.DataFrame:
    """Load a NASA POWER export file."""
    return load_tabular_file(file_path, **kwargs)


def select_department_variables(
    dataframe: pd.DataFrame,
    departments: list[str],
    variables: list[str],
    department_column: str = "department",
    variable_column: str = "variable",
) -> pd.DataFrame:
    """Subset climate data to selected departments and variables."""
    filtered = dataframe.copy()
    if department_column in filtered.columns:
        filtered = filtered.loc[filtered[department_column].isin(departments)]
    if variable_column in filtered.columns:
        filtered = filtered.loc[filtered[variable_column].isin(variables)]
    return filtered.copy()
