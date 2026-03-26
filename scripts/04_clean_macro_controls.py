"""Clean macro control series for the cocoa volatility project."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.file_utils import load_yaml, write_dataframe
from src.utils.logging_utils import get_project_logger, log_dataframe_shape

PATHS = load_yaml(ROOT / "config" / "paths.yaml")


def load_latest_csv(raw_directory: Path, pattern: str) -> pd.DataFrame:
    """Load the latest raw CSV matching a pattern."""
    candidates = sorted(raw_directory.glob(pattern))
    if not candidates:
        return pd.DataFrame()
    return pd.read_csv(candidates[-1])


def aggregate_daily_to_monthly(frame: pd.DataFrame, value_column: str) -> pd.DataFrame:
    """Aggregate a daily series to month-start averages."""
    if frame.empty:
        return pd.DataFrame(columns=["date", value_column])

    aggregated = frame.copy()
    aggregated["date"] = pd.to_datetime(aggregated["date"])
    aggregated[value_column] = pd.to_numeric(aggregated[value_column], errors="coerce")
    aggregated = (
        aggregated.assign(date=aggregated["date"].dt.to_period("M").dt.to_timestamp())
        .groupby("date", as_index=False)[value_column]
        .mean()
    )
    return aggregated


def combine_preferred_monthly_with_daily_fill(
    preferred_monthly: pd.DataFrame,
    daily_series: pd.DataFrame,
    value_column: str,
) -> pd.DataFrame:
    """Keep official monthly values and fill later gaps from daily averages."""
    monthly = preferred_monthly[["date", value_column]].copy() if not preferred_monthly.empty else pd.DataFrame()
    daily_monthly = aggregate_daily_to_monthly(daily_series, value_column)

    if monthly.empty:
        return daily_monthly
    if daily_monthly.empty:
        return monthly

    combined = pd.concat([monthly, daily_monthly], ignore_index=True)
    combined["priority"] = combined[value_column].notna().astype(int)
    combined["source_priority"] = combined.index >= len(monthly)
    combined = combined.sort_values(["date", "priority", "source_priority"], ascending=[True, False, True])
    combined = combined.drop_duplicates(subset=["date"], keep="first")
    return combined.drop(columns=["priority", "source_priority"]).reset_index(drop=True)


def main() -> None:
    """Build monthly macro controls from the latest raw downloads."""
    logger = get_project_logger("04_clean_macro_controls", ROOT / PATHS["output_logs"])
    raw_directory = ROOT / PATHS["raw_macro"]

    trm_daily = load_latest_csv(raw_directory, "*_banrep_trm_daily_raw.csv")
    brent_monthly = load_latest_csv(raw_directory, "*_eia_brent_monthly_raw.csv")
    brent_daily = load_latest_csv(raw_directory, "*_eia_brent_daily_raw.csv")

    if not trm_daily.empty:
        trm_monthly = aggregate_daily_to_monthly(trm_daily, "cop_usd_exchange_rate")
    else:
        trm_monthly = pd.DataFrame(columns=["date", "cop_usd_exchange_rate"])

    if not brent_monthly.empty:
        brent_monthly["date"] = pd.to_datetime(brent_monthly["date"])
        brent_monthly["brent_oil_usd_bbl"] = pd.to_numeric(brent_monthly["brent_oil_usd_bbl"], errors="coerce")
        brent_monthly = brent_monthly[["date", "brent_oil_usd_bbl"]].copy()
        brent_monthly = combine_preferred_monthly_with_daily_fill(
            preferred_monthly=brent_monthly,
            daily_series=brent_daily,
            value_column="brent_oil_usd_bbl",
        )
    elif not brent_daily.empty:
        brent_monthly = aggregate_daily_to_monthly(brent_daily, "brent_oil_usd_bbl")
    else:
        brent_monthly = pd.DataFrame(columns=["date", "brent_oil_usd_bbl"])

    cleaned = trm_monthly.merge(brent_monthly, on="date", how="outer").sort_values("date").reset_index(drop=True)
    cleaned["frequency"] = "monthly"
    output_path = ROOT / PATHS["data_interim_cleaned"] / "macro_controls_cleaned.csv"
    write_dataframe(cleaned, output_path)
    log_dataframe_shape(logger, "macro_controls_cleaned", cleaned)


if __name__ == "__main__":
    main()
