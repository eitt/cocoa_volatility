"""Download and parse helpers for Colombian domestic cocoa price series."""

from __future__ import annotations

from datetime import date
from io import StringIO
from pathlib import Path
import re
import unicodedata

import pandas as pd
import requests

from src.utils.file_utils import ensure_directory

MONTH_NAME_TO_NUMBER = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


def fetch_text(url: str, timeout: int = 120, headers: dict[str, str] | None = None) -> str:
    """Fetch a text payload from a URL."""
    response = requests.get(url, timeout=timeout, headers=headers or {"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    return response.content.decode("utf-8", errors="ignore")


def write_text(content: str, output_path: str | Path) -> Path:
    """Write UTF-8 text content to disk."""
    path = Path(output_path)
    ensure_directory(path.parent)
    path.write_text(content, encoding="utf-8")
    return path


def normalize_agronet_text(value: str) -> str:
    """Normalize AgroNet labels with whitespace and accent cleanup."""
    text = unicodedata.normalize("NFKD", str(value)).replace("\xa0", " ")
    text = "".join(character for character in text if not unicodedata.combining(character))
    text = "".join(character for character in text if character.isprintable())
    text = text.lower().strip()
    text = re.sub(r"(?<=\d)de\b", " de", text)
    text = re.sub(r"(?<=\d)(?=[a-z])", " ", text)
    text = re.sub(r"(?<=[a-z])(?=\d)", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _previous_month(year: int, month: int) -> tuple[int, int]:
    """Return the previous month and year pair."""
    if month == 1:
        return year - 1, 12
    return year, month - 1


def parse_agronet_week_range(label: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Parse the weekly date label published on the AgroNet cacao page."""
    text = normalize_agronet_text(label)
    patterns = [
        r"^(?P<d1>\d{1,2})\s+al\s+(?P<d2>\d{1,2})\s+de\s+(?P<m2>[a-z]+)\s+de\s+(?P<y>\d{4})$",
        r"^(?P<d1>\d{1,2})\s+de\s+(?P<m1>[a-z]+)\s+al\s+(?P<d2>\d{1,2})\s+de\s+(?P<m2>[a-z]+)\s+de\s+(?P<y>\d{4})$",
        r"^(?P<d1>\d{1,2})\s+(?P<m1>[a-z]+)\s+al\s+(?P<d2>\d{1,2})\s+de\s+(?P<m2>[a-z]+)\s+de\s+(?P<y>\d{4})$",
        r"^(?P<d1>\d{1,2})\s+de\s+(?P<m1>[a-z]+)\s+de\s+(?P<y1>\d{4})\s+al\s+(?P<d2>\d{1,2})\s+de\s+(?P<m2>[a-z]+)\s+de\s+(?P<y2>\d{4})$",
        r"^(?P<d1>\d{1,2})\s+(?P<m1>[a-z]+)\s+de\s+(?P<y1>\d{4})\s+al\s+(?P<d2>\d{1,2})\s+(?P<m2>[a-z]+)\s+de\s+(?P<y2>\d{4})$",
    ]

    for pattern_index, pattern in enumerate(patterns):
        match = re.match(pattern, text)
        if not match:
            continue

        groups = match.groupdict()
        if pattern_index == 0:
            end_year = int(groups["y"])
            end_month = MONTH_NAME_TO_NUMBER[groups["m2"]]
            end_day = int(groups["d2"])
            start_day = int(groups["d1"])
            start_year, start_month = (end_year, end_month) if start_day <= end_day else _previous_month(end_year, end_month)
        elif pattern_index in {1, 2}:
            end_year = int(groups["y"])
            end_month = MONTH_NAME_TO_NUMBER[groups["m2"]]
            end_day = int(groups["d2"])
            start_month = MONTH_NAME_TO_NUMBER[groups["m1"]]
            start_day = int(groups["d1"])
            start_year = end_year if start_month <= end_month else end_year - 1
        else:
            start_year = int(groups["y1"])
            start_month = MONTH_NAME_TO_NUMBER[groups["m1"]]
            start_day = int(groups["d1"])
            end_year = int(groups["y2"])
            end_month = MONTH_NAME_TO_NUMBER[groups["m2"]]
            end_day = int(groups["d2"])

        start_date = pd.Timestamp(date(start_year, start_month, start_day))
        end_date = pd.Timestamp(date(end_year, end_month, end_day))
        return start_date, end_date

    raise ValueError(f"Unsupported AgroNet week label: {label}")


def parse_agronet_price_label(value: str) -> float:
    """Convert an AgroNet price label such as `$9.249,20/kg` into a float."""
    text = normalize_agronet_text(value)
    text = text.replace("$", "").replace("/kg", "").replace("cop", "")
    text = re.sub(r"[^0-9,.-]", "", text)
    if not text:
        raise ValueError(f"Unsupported AgroNet price label: {value}")

    if "," in text:
        normalized = text.replace(".", "").replace(",", ".")
    elif text.count(".") > 1:
        integer_part, decimal_part = text.rsplit(".", 1)
        normalized = integer_part.replace(".", "") + "." + decimal_part
    else:
        normalized = text

    return float(normalized)


def extract_agronet_weekly_cacao_series(
    html_text: str,
    source_url: str | None = None,
    source_name: str = "AgroNet / Ministerio de Agricultura y Desarrollo Rural",
    source_dataset: str = "Precio de referencia semanal de compra de cacao",
) -> pd.DataFrame:
    """Parse the AgroNet cacao page into a weekly domestic cocoa price table."""
    tables = pd.read_html(StringIO(html_text))
    if not tables:
        raise ValueError("No HTML tables were found in the AgroNet cacao page.")

    weekly = tables[0].iloc[:, :2].copy()
    weekly.columns = ["date_label_raw", "price_label_raw"]
    weekly["date_label_normalized"] = weekly["date_label_raw"].map(normalize_agronet_text)
    weekly = weekly.loc[weekly["date_label_normalized"] != "fecha"].copy()
    weekly["date_label_raw"] = weekly["date_label_normalized"]
    weekly["price_label_raw"] = weekly["price_label_raw"].map(normalize_agronet_text)

    parsed_ranges = weekly["date_label_raw"].map(parse_agronet_week_range)
    weekly["week_start_date"] = [parsed_range[0] for parsed_range in parsed_ranges]
    weekly["date"] = [parsed_range[1] for parsed_range in parsed_ranges]
    weekly["price"] = weekly["price_label_raw"].map(parse_agronet_price_label)

    weekly = weekly.sort_values("date").reset_index(drop=True)
    weekly["frequency"] = "weekly"
    weekly["product_name"] = "cacao"
    weekly["market"] = "colombia_reference_purchase_price"
    weekly["unit"] = "cop/kg"
    weekly["currency"] = "COP"
    weekly["series_name"] = "colombia_cocoa_price_cop_kg"
    weekly["source_name"] = source_name
    weekly["source_dataset"] = source_dataset
    weekly["source_url"] = source_url

    return weekly[
        [
            "date",
            "week_start_date",
            "date_label_raw",
            "price_label_raw",
            "price",
            "frequency",
            "product_name",
            "market",
            "unit",
            "currency",
            "series_name",
            "source_name",
            "source_dataset",
            "source_url",
        ]
    ].copy()


def aggregate_agronet_weekly_to_monthly(weekly: pd.DataFrame) -> pd.DataFrame:
    """Aggregate AgroNet weekly cocoa prices to monthly means."""
    if weekly.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "price",
                "observation_count",
                "frequency",
                "product_name",
                "market",
                "unit",
                "currency",
                "series_name",
                "source_name",
                "source_dataset",
                "source_url",
            ]
        )

    monthly = weekly.copy()
    monthly["date"] = pd.to_datetime(monthly["date"]).dt.to_period("M").dt.to_timestamp()
    monthly = (
        monthly.groupby("date", as_index=False)
        .agg(
            price=("price", "mean"),
            observation_count=("price", "size"),
        )
        .sort_values("date")
        .reset_index(drop=True)
    )
    monthly["price"] = monthly["price"].round(2)

    first_row = weekly.iloc[0]
    monthly["frequency"] = "monthly"
    monthly["product_name"] = first_row["product_name"]
    monthly["market"] = first_row["market"]
    monthly["unit"] = first_row["unit"]
    monthly["currency"] = first_row["currency"]
    monthly["series_name"] = first_row["series_name"]
    monthly["source_name"] = first_row["source_name"]
    monthly["source_dataset"] = first_row["source_dataset"]
    monthly["source_url"] = first_row["source_url"]
    return monthly
