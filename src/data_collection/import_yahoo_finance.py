"""Import helpers for Yahoo Finance chart payloads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def load_yahoo_chart_payload(file_path: str | Path) -> dict[str, Any]:
    """Load a Yahoo Finance chart JSON payload from disk."""
    return json.loads(Path(file_path).read_text(encoding="utf-8"))


def normalize_yahoo_chart_payload(
    payload: dict[str, Any],
    frequency: str,
    symbol: str,
    source_url: str | None = None,
    source_institution: str = "Yahoo Finance",
    source_dataset: str = "ICE cocoa futures continuous contract",
) -> pd.DataFrame:
    """Convert a Yahoo Finance chart payload into a tidy dataframe."""
    chart = payload.get("chart", {})
    results = chart.get("result") or []
    if not results:
        return pd.DataFrame()

    result = results[0]
    timestamps = result.get("timestamp") or []
    indicators = result.get("indicators", {})
    quote_list = indicators.get("quote") or [{}]
    adjclose_list = indicators.get("adjclose") or [{}]
    quote = quote_list[0] if quote_list else {}
    adjclose = adjclose_list[0] if adjclose_list else {}

    output = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": quote.get("open", []),
            "high": quote.get("high", []),
            "low": quote.get("low", []),
            "close": quote.get("close", []),
            "volume": quote.get("volume", []),
            "adj_close": adjclose.get("adjclose", []),
        }
    )
    if output.empty:
        return output

    output["date"] = pd.to_datetime(output["timestamp"], unit="s", utc=True).dt.tz_localize(None).dt.normalize()
    output["world_cocoa_futures_usd_mt"] = pd.to_numeric(output["close"], errors="coerce")
    output["open"] = pd.to_numeric(output["open"], errors="coerce")
    output["high"] = pd.to_numeric(output["high"], errors="coerce")
    output["low"] = pd.to_numeric(output["low"], errors="coerce")
    output["close"] = pd.to_numeric(output["close"], errors="coerce")
    output["adj_close"] = pd.to_numeric(output["adj_close"], errors="coerce")
    output["volume"] = pd.to_numeric(output["volume"], errors="coerce")
    output["symbol"] = symbol
    output["frequency"] = frequency
    output["currency"] = result.get("meta", {}).get("currency", "USD")
    output["unit"] = "USD/metric_ton"
    output["source_institution"] = source_institution
    output["source_dataset"] = source_dataset
    output["source_url"] = source_url
    output["series_name"] = "world_cocoa_futures_usd_mt"

    columns = [
        "date",
        "symbol",
        "frequency",
        "world_cocoa_futures_usd_mt",
        "open",
        "high",
        "low",
        "close",
        "adj_close",
        "volume",
        "currency",
        "unit",
        "series_name",
        "source_institution",
        "source_dataset",
        "source_url",
    ]
    return output[columns].dropna(subset=["date"]).reset_index(drop=True)
