"""NASA POWER download and normalization helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlencode

import pandas as pd
import requests

API_ROOT = "https://power.larc.nasa.gov/api/temporal"
SUPPORTED_FREQUENCIES = {"daily", "monthly"}


def build_nasa_power_point_url(
    frequency: str,
    parameters: Sequence[str],
    latitude: float,
    longitude: float,
    start: str,
    end: str,
    community: str = "AG",
    output_format: str = "JSON",
) -> str:
    """Build a NASA POWER point API URL for daily or monthly time series."""
    normalized_frequency = frequency.lower()
    if normalized_frequency not in SUPPORTED_FREQUENCIES:
        raise ValueError(f"Unsupported NASA POWER frequency: {frequency}")
    if not parameters:
        raise ValueError("At least one NASA POWER parameter is required.")

    query = urlencode(
        {
            "parameters": ",".join(parameters),
            "community": community,
            "longitude": f"{longitude:.7f}",
            "latitude": f"{latitude:.7f}",
            "format": output_format.upper(),
            "start": start,
            "end": end,
        }
    )
    return f"{API_ROOT}/{normalized_frequency}/point?{query}"


def fetch_nasa_power_point_json(
    url: str,
    timeout: int = 120,
    request_session: requests.Session | None = None,
) -> dict[str, Any]:
    """Fetch a NASA POWER JSON response and validate the basic structure."""
    session = request_session or requests.Session()
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError("NASA POWER response was not a JSON object.")
    if "properties" not in payload:
        raise ValueError("NASA POWER response did not include properties.")
    return payload


def normalize_nasa_power_payload(
    payload: Mapping[str, Any],
    frequency: str,
    location_metadata: Mapping[str, Any] | None = None,
    source_url: str | None = None,
) -> pd.DataFrame:
    """Convert a NASA POWER response into a tidy long dataframe."""
    normalized_frequency = frequency.lower()
    if normalized_frequency not in SUPPORTED_FREQUENCIES:
        raise ValueError(f"Unsupported NASA POWER frequency: {frequency}")

    properties = payload.get("properties", {})
    parameter_block = properties.get("parameter", {})
    parameter_metadata = payload.get("parameters", {})
    header = payload.get("header") or properties.get("header", {})
    coordinates = list(payload.get("geometry", {}).get("coordinates", []))
    longitude = coordinates[0] if len(coordinates) > 0 else None
    latitude = coordinates[1] if len(coordinates) > 1 else None
    elevation_m = coordinates[2] if len(coordinates) > 2 else None
    fill_value = header.get("fill_value", -999.0)
    shared_metadata = dict(location_metadata or {})

    records: list[dict[str, Any]] = []
    for variable, series in parameter_block.items():
        variable_metadata = parameter_metadata.get(variable, {})
        for period_code, raw_value in series.items():
            date_value = parse_nasa_power_period(period_code, normalized_frequency)
            if date_value is None:
                continue

            value = None if raw_value == fill_value else raw_value
            record = {
                **shared_metadata,
                "frequency": normalized_frequency,
                "date": date_value,
                "period_code": str(period_code),
                "variable": variable,
                "value": value,
                "unit": variable_metadata.get("units"),
                "variable_long_name": variable_metadata.get("longname"),
                "latitude": latitude,
                "longitude": longitude,
                "elevation_m": elevation_m,
                "time_standard": header.get("time_standard"),
                "request_start": header.get("start"),
                "request_end": header.get("end"),
                "source_url": source_url,
            }
            records.append(record)

    if not records:
        return pd.DataFrame()

    output = pd.DataFrame.from_records(records)
    output["date"] = pd.to_datetime(output["date"])
    output = output.sort_values(["date", "variable"]).reset_index(drop=True)
    return output


def parse_nasa_power_period(period_code: str | int, frequency: str) -> pd.Timestamp | None:
    """Parse NASA POWER period labels and drop annual summaries from monthly data."""
    normalized_frequency = frequency.lower()
    code = str(period_code)

    if normalized_frequency == "daily":
        return pd.to_datetime(code, format="%Y%m%d")

    if normalized_frequency == "monthly":
        if len(code) == 6 and code.endswith("13"):
            return None
        return pd.to_datetime(f"{code}01", format="%Y%m%d")

    raise ValueError(f"Unsupported NASA POWER frequency: {frequency}")


def pivot_nasa_power_long_to_wide(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Pivot a tidy NASA POWER dataframe into a wide time-series table."""
    if dataframe.empty:
        return dataframe.copy()

    metadata_columns = [
        column
        for column in dataframe.columns
        if column not in {"variable", "value", "unit", "variable_long_name"}
    ]
    wide = (
        dataframe.pivot_table(
            index=metadata_columns,
            columns="variable",
            values="value",
            aggfunc="first",
        )
        .reset_index()
        .rename_axis(columns=None)
    )
    return wide.sort_values("date").reset_index(drop=True)
