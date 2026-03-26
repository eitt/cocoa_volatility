"""Import helpers for World Bank commodity price files."""

from __future__ import annotations

import pandas as pd

from src.data_collection.load_local_files import load_tabular_file


def load_world_bank_prices(file_path: str, **kwargs) -> pd.DataFrame:
    """Load a World Bank commodity file."""
    return load_tabular_file(file_path, **kwargs)


def reshape_world_bank_prices(
    dataframe: pd.DataFrame,
    date_column: str = "date",
    value_column: str = "price",
    series_name: str = "world_cocoa_price_usd_mt",
) -> pd.DataFrame:
    """Return a long-form dataframe with a consistent series label."""
    reshaped = dataframe.copy()
    if date_column not in reshaped.columns or value_column not in reshaped.columns:
        return reshaped
    reshaped["series_name"] = series_name
    return reshaped[[date_column, value_column, "series_name"]].copy()


def extract_world_bank_cocoa_monthly_series(file_path: str) -> pd.DataFrame:
    """Extract the cocoa monthly series from the World Bank Pink Sheet workbook."""
    raw = pd.read_excel(file_path, sheet_name="Monthly Prices", header=None)
    header_row = raw.iloc[4].fillna("")
    unit_row = raw.iloc[5].fillna("")

    cocoa_column = None
    for column_index, column_label in header_row.items():
        if str(column_label).strip().lower() == "cocoa":
            cocoa_column = column_index
            break
    if cocoa_column is None:
        raise ValueError("Could not locate the Cocoa column in the World Bank workbook.")

    rows = raw.iloc[6:, [0, cocoa_column]].copy()
    rows.columns = ["period_code", "world_cocoa_price_usd_kg"]
    rows["period_code"] = rows["period_code"].astype(str).str.strip()
    rows = rows.loc[rows["period_code"].str.fullmatch(r"\d{4}M\d{2}")].copy()
    rows["world_cocoa_price_usd_kg"] = pd.to_numeric(
        rows["world_cocoa_price_usd_kg"].replace({"…": None}),
        errors="coerce",
    )
    rows["date"] = pd.to_datetime(
        rows["period_code"].str.replace("M", "-", regex=False) + "-01",
        errors="coerce",
    )
    rows["world_cocoa_price_usd_mt"] = rows["world_cocoa_price_usd_kg"] * 1000.0
    rows["currency"] = "USD"
    rows["unit"] = "USD/metric_ton"
    rows["frequency"] = "monthly"
    rows["series_name"] = "world_cocoa_price_usd_mt"
    rows["source_institution"] = "World Bank Prospects Group"
    rows["source_dataset"] = "Commodities Price Data (The Pink Sheet)"
    rows["source_unit_raw"] = str(unit_row.iloc[cocoa_column]).strip()
    return rows[
        [
            "date",
            "period_code",
            "world_cocoa_price_usd_kg",
            "world_cocoa_price_usd_mt",
            "currency",
            "unit",
            "frequency",
            "series_name",
            "source_institution",
            "source_dataset",
            "source_unit_raw",
        ]
    ].dropna(subset=["date"]).reset_index(drop=True)
