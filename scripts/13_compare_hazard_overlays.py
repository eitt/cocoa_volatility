from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
PANEL_PATH = ROOT / "reports" / "v2" / "intermediate" / "v3_integrated_panel.csv"
EVENT_PANEL_PATH = ROOT / "reports" / "v2" / "intermediate" / "04_monthly_event_panel.csv"
OUTPUT_DIR = ROOT / "paper" / "tables"


def _nested_window() -> pd.DataFrame:
    panel = pd.read_csv(PANEL_PATH, parse_dates=["date"])
    panel["month"] = pd.to_datetime(panel["date"])

    events = pd.read_csv(EVENT_PANEL_PATH, parse_dates=["month"])
    merged = panel.merge(events, on="month", how="left")

    mask = (merged["month"] >= "2021-08-01") & (merged["month"] <= "2024-07-01")
    df = merged.loc[mask].copy()
    df["colombia_return"] = df["colombia_cocoa_price_cop_kg_log_return"]
    df["world_volatility"] = df["world_return"].rolling(12, min_periods=6).std()
    return df


def _screen_direct_signals(df: pd.DataFrame) -> pd.DataFrame:
    signals = {
        "earthquake_events": "Earthquake events",
        "geophysical_events": "Geophysical events",
        "hydrometeorological_events": "Hydrometeorological events",
        "total_events": "Total recorded events",
    }
    records: list[dict[str, object]] = []
    for column, label in signals.items():
        series = df[column].fillna(0.0).astype(float)
        peak_idx = int(series.idxmax())
        peak_month = pd.Timestamp(df.loc[peak_idx, "month"]).date().isoformat()
        records.append(
            {
                "signal": column,
                "label": label,
                "months": int(series.shape[0]),
                "nonzero_months": int((series > 0).sum()),
                "zero_share": float((series == 0).mean()),
                "total_value": float(series.sum()),
                "mean_value": float(series.mean()),
                "std_value": float(series.std(ddof=1)),
                "peak_month": peak_month,
                "peak_value": float(series.max()),
            }
        )
    return pd.DataFrame(records)


def _fit_return_model(data: pd.DataFrame, signal_column: str) -> dict[str, float]:
    model_df = data[
        ["colombia_return", "world_return", "fx_return", "oil_return", signal_column]
    ].dropna().copy()
    model_df["signal_z"] = stats.zscore(model_df[signal_column].astype(float), nan_policy="omit")
    x = sm.add_constant(model_df[["world_return", "fx_return", "oil_return", "signal_z"]])
    y = model_df["colombia_return"]
    model = sm.OLS(y, x).fit(cov_type="HAC", cov_kwds={"maxlags": 1})
    return {
        "return_nobs": float(model.nobs),
        "return_adj_r2": float(model.rsquared_adj),
        "return_aic": float(model.aic),
        "return_signal_coef": float(model.params["signal_z"]),
        "return_signal_p": float(model.pvalues["signal_z"]),
        "return_world_coef": float(model.params["world_return"]),
        "return_world_p": float(model.pvalues["world_return"]),
    }


def _fit_volatility_model(data: pd.DataFrame, signal_column: str) -> dict[str, float]:
    model_df = data[
        ["colombia_cocoa_price_cop_kg_log_return_rolling_volatility", "world_volatility", signal_column]
    ].dropna().copy()
    model_df["signal_z"] = stats.zscore(model_df[signal_column].astype(float), nan_policy="omit")
    x = sm.add_constant(model_df[["world_volatility", "signal_z"]])
    y = model_df["colombia_cocoa_price_cop_kg_log_return_rolling_volatility"]
    model = sm.OLS(y, x).fit(cov_type="HAC", cov_kwds={"maxlags": 1})
    return {
        "volatility_nobs": float(model.nobs),
        "volatility_adj_r2": float(model.rsquared_adj),
        "volatility_aic": float(model.aic),
        "volatility_signal_coef": float(model.params["signal_z"]),
        "volatility_signal_p": float(model.pvalues["signal_z"]),
        "volatility_world_coef": float(model.params["world_volatility"]),
        "volatility_world_p": float(model.pvalues["world_volatility"]),
    }


def _compare_overlay_models(df: pd.DataFrame) -> pd.DataFrame:
    signals = {
        "hydrometeorological_events": ("Direct", "Hydrometeorological events"),
        "geophysical_events": ("Direct", "Geophysical events"),
        "total_events": ("Direct", "Total recorded events"),
        "disaster_pressure": ("Composite", "PCA disaster pressure"),
    }
    records: list[dict[str, object]] = []
    for column, (signal_type, label) in signals.items():
        return_stats = _fit_return_model(df, column)
        volatility_stats = _fit_volatility_model(df, column)
        peak_idx = int(df[column].astype(float).idxmax())
        records.append(
            {
                "signal": column,
                "signal_type": signal_type,
                "label": label,
                "peak_month": pd.Timestamp(df.loc[peak_idx, "month"]).date().isoformat(),
                **return_stats,
                **volatility_stats,
            }
        )
    return pd.DataFrame(records).sort_values(
        ["signal_type", "return_adj_r2", "volatility_adj_r2"],
        ascending=[True, False, False],
    )


def _write_table(df: pd.DataFrame, stem: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUTPUT_DIR / f"{stem}.csv"
    json_path = OUTPUT_DIR / f"{stem}.json"
    df.to_csv(csv_path, index=False)
    json_path.write_text(df.to_json(orient="records", indent=2), encoding="utf-8")


def main() -> None:
    df = _nested_window()
    screening = _screen_direct_signals(df)
    comparison = _compare_overlay_models(df)
    _write_table(screening, "table_hazard_signal_screening")
    _write_table(comparison, "table_hazard_overlay_model_comparison")
    summary = {
        "nested_window_start": "2021-08-01",
        "nested_window_end": "2024-07-01",
        "rows": int(df.shape[0]),
        "best_direct_signal_by_return_adj_r2": comparison.loc[
            comparison["signal_type"] == "Direct", "signal"
        ].iloc[0],
        "best_direct_signal_by_volatility_adj_r2": comparison.loc[
            comparison["signal_type"] == "Direct"
        ].sort_values("volatility_adj_r2", ascending=False)["signal"].iloc[0],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
