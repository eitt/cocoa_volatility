from __future__ import annotations

import pandas as pd

from src.data_collection.import_sipsa import clean_sipsa_columns, select_cocoa_rows
from src.data_processing.clean_colombia_prices import clean_colombia_price_columns


def test_clean_sipsa_columns_and_select_cocoa_rows() -> None:
    dataframe = pd.DataFrame(
        {
            "Fecha": ["2024-01-01", "2024-01-01"],
            "Producto": ["Cacao en grano", "Cafe"],
            "Precio": [12000, 8000],
        }
    )

    cleaned = clean_sipsa_columns(dataframe)
    cleaned = clean_colombia_price_columns(cleaned, {"fecha": "date", "producto": "product_name"})
    cocoa_only = select_cocoa_rows(cleaned, product_column="product_name")

    assert list(cocoa_only["product_name"]) == ["Cacao en grano"]

