"""Download and parse helpers for macro control series."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from urllib.parse import urlencode

import pandas as pd
import requests

from src.utils.file_utils import ensure_directory

EIA_MONTH_MAP = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


def build_banrep_trm_url(
    series_id: int,
    tipo_dato: int = 0,
    cant_datos: int = 35,
    frecuencia_datos: str = "year",
) -> str:
    """Build the official BanRep TRM historical-series URL."""
    query = urlencode(
        {
            "idSerie": series_id,
            "tipoDato": tipo_dato,
            "cantDatos": cant_datos,
            "frecuenciaDatos": frecuencia_datos,
        }
    )
    base = "https://suameca.banrep.gov.co/estadisticas-economicas-back/rest/estadisticaEconomicaRestService"
    return f"{base}/consultaInformacionSerieXTipoDatoXFechaDesde?{query}"


def fetch_json(url: str, timeout: int = 120, headers: dict[str, str] | None = None) -> dict | list:
    """Fetch a JSON payload from a URL."""
    response = requests.get(url, timeout=timeout, headers=headers or {"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    return response.json()


def fetch_text(url: str, timeout: int = 120, headers: dict[str, str] | None = None) -> str:
    """Fetch a text payload from a URL."""
    response = requests.get(url, timeout=timeout, headers=headers or {"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    return response.text


def write_json_payload(payload: dict | list, output_path: str | Path) -> Path:
    """Write a JSON payload to disk."""
    path = Path(output_path)
    ensure_directory(path.parent)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_text_payload(content: str, output_path: str | Path) -> Path:
    """Write raw text content to disk."""
    path = Path(output_path)
    ensure_directory(path.parent)
    path.write_text(content, encoding="utf-8")
    return path


def normalize_banrep_trm_payload(payload: list[dict], source_url: str | None = None) -> pd.DataFrame:
    """Normalize the BanRep TRM payload into a daily dataframe."""
    if not payload:
        return pd.DataFrame(
            columns=[
                "date",
                "cop_usd_exchange_rate",
                "frequency",
                "unit",
                "series_name",
                "source_institution",
                "source_dataset",
                "source_url",
            ]
        )

    series = payload[0]
    rows = pd.DataFrame(series.get("data") or [], columns=["timestamp_ms", "cop_usd_exchange_rate"])
    rows["date"] = (
        pd.to_datetime(rows["timestamp_ms"], unit="ms", utc=True)
        .dt.tz_convert("America/Bogota")
        .dt.tz_localize(None)
        .dt.normalize()
    )
    rows["cop_usd_exchange_rate"] = pd.to_numeric(rows["cop_usd_exchange_rate"], errors="coerce")
    rows["frequency"] = "daily"
    rows["unit"] = series.get("unidadCorta", "COP/USD")
    rows["series_name"] = "cop_usd_exchange_rate"
    rows["source_institution"] = "Banco de la República / Superintendencia Financiera de Colombia"
    rows["source_dataset"] = series.get("nombre", "Tasa Representativa del Mercado (TRM)")
    rows["source_url"] = source_url
    return rows[
        [
            "date",
            "cop_usd_exchange_rate",
            "frequency",
            "unit",
            "series_name",
            "source_institution",
            "source_dataset",
            "source_url",
        ]
    ].copy()


def _find_eia_monthly_table(html_text: str) -> pd.DataFrame:
    """Locate the Brent monthly matrix table in the EIA history page."""
    for table in pd.read_html(StringIO(html_text)):
        normalized_columns = [str(column).strip() for column in table.columns]
        if normalized_columns[:4] == ["Year", "Jan", "Feb", "Mar"]:
            return table.copy()
    raise ValueError("Could not locate the EIA monthly Brent history table.")


def _find_eia_daily_table(html_text: str) -> pd.DataFrame:
    """Locate the Brent daily week-grid table in the EIA history page."""
    for table in pd.read_html(StringIO(html_text)):
        normalized_columns = [str(column).strip() for column in table.columns]
        if normalized_columns[:3] == ["Week Of", "Mon", "Tue"] and len(table) > 10:
            return table.copy()
    raise ValueError("Could not locate the EIA daily Brent history table.")


def parse_eia_brent_monthly_history(html_text: str, source_url: str | None = None) -> pd.DataFrame:
    """Parse the official EIA monthly Brent history page."""
    table = _find_eia_monthly_table(html_text)
    table = table.dropna(subset=["Year"]).copy()
    table["Year"] = pd.to_numeric(table["Year"], errors="coerce")
    month_columns = [month for month in EIA_MONTH_MAP if month in table.columns]

    records: list[dict[str, object]] = []
    for _, row in table.iterrows():
        year = int(row["Year"])
        for month_label in month_columns:
            value = pd.to_numeric(row[month_label], errors="coerce")
            if pd.isna(value):
                continue
            records.append(
                {
                    "date": pd.Timestamp(year=year, month=EIA_MONTH_MAP[month_label], day=1),
                    "brent_oil_usd_bbl": float(value),
                    "frequency": "monthly",
                    "unit": "USD/barrel",
                    "series_name": "brent_oil_usd_bbl",
                    "source_institution": "U.S. Energy Information Administration",
                    "source_dataset": "Europe Brent Spot Price FOB",
                    "source_url": source_url,
                }
            )

    return pd.DataFrame.from_records(records).sort_values("date").reset_index(drop=True)


def _parse_eia_week_label(label: str) -> pd.Timestamp:
    """Parse the week label used in the EIA daily Brent history table."""
    normalized = " ".join(str(label).split())
    year_text, remainder = normalized.split(" ", 1)
    start_text, _ = remainder.split(" to ", 1)
    month_text, day_text = start_text.split("-")
    month = EIA_MONTH_MAP[month_text.strip()]
    day = int(day_text.strip())
    return pd.Timestamp(year=int(year_text), month=month, day=day)


def parse_eia_brent_daily_history(html_text: str, source_url: str | None = None) -> pd.DataFrame:
    """Parse the official EIA daily Brent history page."""
    table = _find_eia_daily_table(html_text)
    table = table.dropna(subset=["Week Of"], how="all").copy()
    weekday_columns = ["Mon", "Tue", "Wed", "Thu", "Fri"]

    records: list[dict[str, object]] = []
    for _, row in table.iterrows():
        week_label = str(row["Week Of"]).strip()
        if not week_label or week_label == "Week Of" or not any(character.isdigit() for character in week_label):
            continue
        start_date = _parse_eia_week_label(week_label)
        for day_offset, weekday_label in enumerate(weekday_columns):
            value = pd.to_numeric(row.get(weekday_label), errors="coerce")
            if pd.isna(value):
                continue
            records.append(
                {
                    "date": start_date + pd.Timedelta(days=day_offset),
                    "brent_oil_usd_bbl": float(value),
                    "frequency": "daily",
                    "unit": "USD/barrel",
                    "series_name": "brent_oil_usd_bbl",
                    "source_institution": "U.S. Energy Information Administration",
                    "source_dataset": "Europe Brent Spot Price FOB",
                    "source_url": source_url,
                }
            )

    return pd.DataFrame.from_records(records).sort_values("date").reset_index(drop=True)
