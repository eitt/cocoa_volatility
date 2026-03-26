from __future__ import annotations

from src.data_collection.download_domestic_cocoa import (
    aggregate_agronet_weekly_to_monthly,
    extract_agronet_weekly_cacao_series,
    parse_agronet_price_label,
    parse_agronet_week_range,
)


def test_parse_agronet_week_range_supports_same_month_labels() -> None:
    start_date, end_date = parse_agronet_week_range("23 al 29 de marzo de 2026")

    assert start_date.strftime("%Y-%m-%d") == "2026-03-23"
    assert end_date.strftime("%Y-%m-%d") == "2026-03-29"


def test_parse_agronet_week_range_supports_cross_month_labels() -> None:
    start_date, end_date = parse_agronet_week_range("27 de octubre al 2 de noviembre de 2025")

    assert start_date.strftime("%Y-%m-%d") == "2025-10-27"
    assert end_date.strftime("%Y-%m-%d") == "2025-11-02"


def test_parse_agronet_price_label_returns_float() -> None:
    assert parse_agronet_price_label("$9.249,20/kg") == 9249.20


def test_parse_agronet_price_label_handles_missing_comma_html_artifacts() -> None:
    assert parse_agronet_price_label("$22.421.720") == 22421.72
    assert parse_agronet_price_label("$38.636.70") == 38636.70


def test_extract_agronet_weekly_cacao_series_and_monthly_aggregation() -> None:
    html = """
    <table>
      <tr><th>Fecha</th><th>Precio</th></tr>
      <tr><td>23 al 29 de marzo de 2026</td><td>$9.249,20/kg</td></tr>
      <tr><td>16 al 22 de marzo de 2026</td><td>$9.255,00/kg</td></tr>
      <tr><td>27 de abril al 3 de mayo de 2026</td><td>$9.100,00/kg</td></tr>
    </table>
    """

    weekly = extract_agronet_weekly_cacao_series(html, source_url="https://example.com/agronet")
    monthly = aggregate_agronet_weekly_to_monthly(weekly)

    assert weekly["price"].tolist() == [9255.0, 9249.2, 9100.0]
    assert weekly["date"].dt.strftime("%Y-%m-%d").tolist() == ["2026-03-22", "2026-03-29", "2026-05-03"]
    assert monthly["date"].dt.strftime("%Y-%m-%d").tolist() == ["2026-03-01", "2026-05-01"]
    assert monthly["price"].round(2).tolist() == [9252.10, 9100.00]
