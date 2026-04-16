"""Input and cleaning helpers for the v2 disaster pipeline."""

from __future__ import annotations

from pathlib import Path
import re

import pandas as pd


MISSING_MARKERS = {
    "",
    "n/a",
    "na",
    "n a",
    "nan",
    "none",
    "null",
    "s/d",
    "nd",
}


def clean_text_value(value: object) -> str | pd.NA:
    """Return a trimmed text value or missing."""
    if pd.isna(value):
        return pd.NA
    text = str(value).replace("\ufeff", "").strip()
    text = re.sub(r"\s+", " ", text)
    if text.lower() in MISSING_MARKERS:
        return pd.NA
    return text


def read_source_csv(path: Path, encoding: str = "utf-8") -> pd.DataFrame:
    """Read the source CSV with the configured encoding."""
    return pd.read_csv(path, encoding=encoding)


def parse_occurrence_dates(series: pd.Series) -> pd.Series:
    """Parse registry occurrence dates with a known text format and a safe fallback."""
    cleaned = series.map(clean_text_value)
    parsed = pd.to_datetime(cleaned, format="%Y %b %d %I:%M:%S %p", errors="coerce")
    needs_fallback = parsed.isna() & cleaned.notna()
    if needs_fallback.any():
        parsed.loc[needs_fallback] = pd.to_datetime(cleaned.loc[needs_fallback], errors="coerce")
    return parsed


def parse_iso_dates(series: pd.Series) -> pd.Series:
    """Parse ISO-style dates from the registry."""
    cleaned = series.map(clean_text_value)
    return pd.to_datetime(cleaned, errors="coerce")


def parse_numeric_series(series: pd.Series) -> pd.Series:
    """Parse numeric fields while handling commas, degree signs, and text noise."""
    cleaned = series.map(clean_text_value)
    normalized = cleaned.astype("string")
    normalized = normalized.str.replace(r"[^0-9,\.\-]", "", regex=True)
    normalized = normalized.str.replace(",", ".", regex=False)
    normalized = normalized.replace({"": pd.NA, "-": pd.NA})
    return pd.to_numeric(normalized, errors="coerce")


def clean_records(raw: pd.DataFrame, schema: dict[str, object], source_file: Path) -> pd.DataFrame:
    """Create a cleaned event-level dataframe while preserving raw Spanish fields."""
    cleaned = raw.copy()
    cleaned["source_file"] = source_file.name
    cleaned["event_id"] = [f"EVT{index + 1:05d}" for index in range(len(cleaned))]

    columns = schema.get("columns", {})
    for raw_column, metadata in columns.items():
        base_name = metadata["base_name"]
        field_type = metadata["type"]
        series = cleaned[raw_column] if raw_column in cleaned.columns else pd.Series(pd.NA, index=cleaned.index)

        if field_type == "datetime_occurrence":
            cleaned[base_name] = parse_occurrence_dates(series)
        elif field_type == "datetime_iso":
            cleaned[base_name] = parse_iso_dates(series)
        elif field_type == "numeric":
            cleaned[base_name] = parse_numeric_series(series)
        elif field_type == "categorical":
            cleaned[f"{base_name}_es"] = series.map(clean_text_value)
        elif field_type == "text":
            cleaned[f"{base_name}_es"] = series.map(clean_text_value)

    cleaned["month"] = cleaned["occurrence_date"].dt.to_period("M").dt.to_timestamp()

    cleaned["human_impact_total"] = cleaned[["injuries", "missing_persons", "deaths"]].fillna(0.0).sum(axis=1)
    cleaned["housing_impact_total"] = cleaned[["destroyed_houses", "damaged_houses"]].fillna(0.0).sum(axis=1)
    cleaned["infrastructure_impact_total"] = cleaned[
        [
            "destroyed_aqueducts",
            "affected_roads",
            "affected_bridges",
            "affected_educational_establishments",
        ]
    ].fillna(0.0).sum(axis=1)
    cleaned["impact_recorded_flag"] = (
        cleaned[["human_impact_total", "housing_impact_total", "infrastructure_impact_total", "affected_hectares"]]
        .fillna(0.0)
        .sum(axis=1)
        > 0
    )
    return cleaned
