"""Aggregation helpers for the v2 disaster pipeline."""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_dataset_overview(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Summarize the registry coverage used by v2."""
    valid_dates = dataframe["occurrence_date"].dropna()
    records = [
        {"metric": "Source rows", "value": int(len(dataframe))},
        {"metric": "Months in observation window", "value": int(dataframe["month"].dropna().nunique())},
        {"metric": "Date range start", "value": valid_dates.min().date().isoformat() if not valid_dates.empty else "Not available"},
        {"metric": "Date range end", "value": valid_dates.max().date().isoformat() if not valid_dates.empty else "Not available"},
        {"metric": "Distinct municipalities", "value": int(dataframe["municipality_en"].fillna("Not reported").nunique())},
        {"metric": "Distinct event types", "value": int(dataframe["event_type_en"].fillna("Not reported").nunique())},
        {"metric": "Earthquake-related events", "value": int(dataframe["earthquake_detected"].fillna(False).sum())},
    ]
    return pd.DataFrame.from_records(records)


def aggregate_monthly_events(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aggregate the classified event registry to a monthly panel and event-type matrix."""
    valid = dataframe.dropna(subset=["month"]).copy()
    if valid.empty:
        return pd.DataFrame(), pd.DataFrame()

    calendar = pd.DataFrame(
        {
            "month": pd.date_range(
                valid["month"].min(),
                valid["month"].max(),
                freq="MS",
            )
        }
    )

    monthly = valid.groupby("month").agg(
        total_events=("event_id", "count"),
        unique_municipalities=("municipality_en", lambda values: values.dropna().nunique()),
        earthquake_events=("earthquake_detected", "sum"),
        affected_families_total=("affected_families", lambda values: values.fillna(0.0).sum()),
        destroyed_houses_total=("destroyed_houses", lambda values: values.fillna(0.0).sum()),
        damaged_houses_total=("damaged_houses", lambda values: values.fillna(0.0).sum()),
        destroyed_aqueducts_total=("destroyed_aqueducts", lambda values: values.fillna(0.0).sum()),
        affected_roads_total=("affected_roads", lambda values: values.fillna(0.0).sum()),
        affected_bridges_total=("affected_bridges", lambda values: values.fillna(0.0).sum()),
        affected_educational_establishments_total=("affected_educational_establishments", lambda values: values.fillna(0.0).sum()),
        affected_hectares_total=("affected_hectares", lambda values: values.fillna(0.0).sum()),
        injuries_total=("injuries", lambda values: values.fillna(0.0).sum()),
        missing_persons_total=("missing_persons", lambda values: values.fillna(0.0).sum()),
        deaths_total=("deaths", lambda values: values.fillna(0.0).sum()),
        human_impact_total=("human_impact_total", lambda values: values.fillna(0.0).sum()),
        housing_impact_total=("housing_impact_total", lambda values: values.fillna(0.0).sum()),
        infrastructure_impact_total=("infrastructure_impact_total", lambda values: values.fillna(0.0).sum()),
    )

    domain_counts = (
        pd.crosstab(valid["month"], valid["hazard_domain_key"])
        .rename(columns=lambda key: f"{key}_events")
        .reset_index()
    )
    event_type_matrix = pd.crosstab(valid["month"], valid["event_type_en"]).reset_index()

    monthly = monthly.reset_index().merge(domain_counts, on="month", how="left")
    monthly = calendar.merge(monthly, on="month", how="left").fillna(0.0)

    integer_like_columns = [
        column
        for column in monthly.columns
        if column.endswith("_events")
        or column in {
            "total_events",
            "unique_municipalities",
            "earthquake_events",
        }
    ]
    for column in integer_like_columns:
        if column in monthly.columns:
            monthly[column] = monthly[column].round(0).astype(int)

    return monthly, event_type_matrix


def build_event_type_summary(dataframe: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Summarize event types in English."""
    full_summary = (
        dataframe.groupby("event_type_en", dropna=False)
        .agg(
            event_count=("event_id", "count"),
            deaths_total=("deaths", lambda values: values.fillna(0.0).sum()),
            injuries_total=("injuries", lambda values: values.fillna(0.0).sum()),
            affected_families_total=("affected_families", lambda values: values.fillna(0.0).sum()),
        )
        .reset_index()
        .sort_values("event_count", ascending=False)
    )
    total_events = full_summary["event_count"].sum()
    summary = full_summary.head(top_n).reset_index(drop=True)
    summary["share_pct"] = np.where(total_events > 0, summary["event_count"] / total_events * 100.0, 0.0)
    return summary


def build_municipality_summary(dataframe: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Summarize municipality exposure."""
    return (
        dataframe.groupby("municipality_en", dropna=False)
        .agg(
            event_count=("event_id", "count"),
            unique_event_types=("event_type_en", lambda values: values.dropna().nunique()),
            deaths_total=("deaths", lambda values: values.fillna(0.0).sum()),
            affected_families_total=("affected_families", lambda values: values.fillna(0.0).sum()),
        )
        .reset_index()
        .sort_values(["event_count", "affected_families_total"], ascending=[False, False])
        .head(top_n)
        .reset_index(drop=True)
    )


def build_translation_strategy_summary(audit_df: pd.DataFrame) -> pd.DataFrame:
    """Summarize how categorical values were translated."""
    if audit_df.empty:
        return pd.DataFrame(columns=["context", "translation_strategy", "value_count"])
    return (
        audit_df.groupby(["context", "translation_strategy"])
        .size()
        .rename("value_count")
        .reset_index()
        .sort_values(["context", "value_count"], ascending=[True, False])
        .reset_index(drop=True)
    )
