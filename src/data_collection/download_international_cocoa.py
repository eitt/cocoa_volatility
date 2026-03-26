"""Download helpers for international cocoa market data."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import requests


def build_yahoo_chart_url(
    symbol: str,
    start_date: str,
    end_date: str,
    interval: str,
    include_adjusted_close: bool = True,
) -> str:
    """Build a Yahoo Finance chart API URL."""
    start_dt = datetime.combine(date.fromisoformat(start_date), time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(date.fromisoformat(end_date) + timedelta(days=1), time.min, tzinfo=timezone.utc)
    start_timestamp = int(start_dt.timestamp())
    end_timestamp = int(end_dt.timestamp())
    query = urlencode(
        {
            "period1": start_timestamp,
            "period2": end_timestamp,
            "interval": interval,
            "includeAdjustedClose": str(include_adjusted_close).lower(),
            "events": "history",
        }
    )
    return f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?{query}"


def fetch_json(url: str, timeout: int = 120, headers: dict[str, str] | None = None) -> dict[str, Any]:
    """Fetch a JSON payload from a URL."""
    response = requests.get(url, timeout=timeout, headers=headers or {"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    return response.json()


def fetch_binary(url: str, timeout: int = 120, headers: dict[str, str] | None = None) -> bytes:
    """Fetch a binary file from a URL."""
    response = requests.get(url, timeout=timeout, headers=headers or {"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    return response.content


def write_json(payload: dict[str, Any], output_path: str | Path) -> Path:
    """Write a JSON payload to disk."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_binary(content: bytes, output_path: str | Path) -> Path:
    """Write binary content to disk."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path
