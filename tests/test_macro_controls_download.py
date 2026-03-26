from __future__ import annotations

from src.data_collection.download_macro_controls import (
    build_banrep_trm_url,
    normalize_banrep_trm_payload,
    parse_eia_brent_monthly_history,
)


def test_build_banrep_trm_url_contains_expected_parameters() -> None:
    url = build_banrep_trm_url(series_id=1, tipo_dato=0, cant_datos=35, frecuencia_datos="year")

    assert "idSerie=1" in url
    assert "tipoDato=0" in url
    assert "cantDatos=35" in url
    assert "frecuenciaDatos=year" in url


def test_normalize_banrep_trm_payload_parses_daily_rows() -> None:
    payload = [
        {
            "nombre": "Tasa Representativa del Mercado (TRM)",
            "unidadCorta": "COP/USD",
            "data": [
                [691218000000, 693.32],
                [691304400000, 693.40],
            ],
        }
    ]

    normalized = normalize_banrep_trm_payload(payload, source_url="https://example.com/trm")

    assert normalized["cop_usd_exchange_rate"].tolist() == [693.32, 693.40]
    assert normalized["series_name"].tolist() == ["cop_usd_exchange_rate", "cop_usd_exchange_rate"]
    assert normalized["unit"].tolist() == ["COP/USD", "COP/USD"]


def test_parse_eia_brent_monthly_history_reads_month_matrix() -> None:
    html = """
    <table>
      <tr><th>Year</th><th>Jan</th><th>Feb</th><th>Mar</th></tr>
      <tr><td>2025</td><td>79.27</td><td>75.44</td><td>72.73</td></tr>
      <tr><td>2026</td><td>66.60</td><td>70.89</td><td></td></tr>
    </table>
    """

    parsed = parse_eia_brent_monthly_history(html, source_url="https://example.com/eia")

    assert parsed["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2025-01-01",
        "2025-02-01",
        "2025-03-01",
        "2026-01-01",
        "2026-02-01",
    ]
    assert parsed["brent_oil_usd_bbl"].tolist() == [79.27, 75.44, 72.73, 66.60, 70.89]
