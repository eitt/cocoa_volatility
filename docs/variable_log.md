# Variable Log

| canonical_name | description | unit | frequency | transform_notes | likely_source |
| --- | --- | --- | --- | --- | --- |
| colombia_cocoa_price_cop_kg | Colombian domestic cocoa price proxy used in the merged panel | COP/kg | weekly aggregated to monthly | aggregate AgroNet weekly values to monthly mean | AgroNet |
| world_cocoa_price_usd_mt | Core international cocoa benchmark price | USD/metric ton | monthly | use as the main world benchmark in merged analysis | World Bank Pink Sheet |
| world_cocoa_futures_usd_mt | Market-based cocoa futures series retained for higher-frequency diagnostics | USD/metric ton | daily and monthly | preserve both daily and monthly versions | Yahoo Finance |
| eu_hicp_chocolate_index | Core EU downstream chocolate indicator | index | monthly | use log level and log difference | Eurostat |
| eu_hicp_cocoa_powdered_chocolate_index | Narrower cocoa-adjacent EU downstream indicator | index | monthly | robustness specification | Eurostat |
| eu_hicp_confectionery_index | Broader confectionery downstream indicator | index | monthly | robustness specification | Eurostat |
| eu_hicp_sweets_aggregate_index | Long-run sweets aggregate indicator | index | monthly | robustness specification | Eurostat |
| fr_hicp_chocolate_index | Longer country-level downstream chocolate indicator | index | monthly | alternative downstream series | Eurostat |
| cop_usd_exchange_rate | Colombian peso to US dollar exchange rate | COP/USD | daily aggregated to monthly | monthly average for merged panel | BanRep |
| brent_oil_usd_bbl | Brent oil macro control | USD/barrel | daily and monthly | preserve daily history and use monthly aligned series | EIA |
| nasa_precipitation_mm_day | NASA POWER precipitation variable | mm/day | monthly | monthly mean from `PRECTOTCORR` | NASA POWER |
| nasa_temperature_c | NASA POWER mean air temperature | degC | monthly | monthly mean from `T2M` | NASA POWER |
| nasa_temperature_max_c | NASA POWER max air temperature | degC | monthly | monthly mean from `T2M_MAX` | NASA POWER |
| nasa_temperature_min_c | NASA POWER min air temperature | degC | monthly | monthly mean from `T2M_MIN` | NASA POWER |
| nasa_relative_humidity_pct | NASA POWER relative humidity | % | monthly | monthly mean from `RH2M` | NASA POWER |
| nasa_wind_speed_ms | NASA POWER wind speed | m/s | monthly | monthly mean from `WS2M` | NASA POWER |
| nasa_surface_solar_radiation_mj_m2_day | NASA POWER surface solar radiation | MJ/m^2/day | monthly | monthly mean from `ALLSKY_SFC_SW_DWN` | NASA POWER |
| weather_stress_index | Composite absolute weather-stress measure built from selected aligned weather z-scores | index | monthly | mean absolute value across selected precipitation, solar-radiation, and max-temperature z-scores | derived from NASA POWER |
| core_market_transmission_shock | Absolute fitted short-run domestic transmission shock from the core aligned return model | index | monthly | absolute fitted value from the core domestic return equation | derived |
| farmer_exposure_index | Exploratory farmer exposure indicator combining domestic volatility, transmission shock, and weather stress | index | monthly | standardized composite exposure measure | derived |
| livelihood_risk_score | Exploratory livelihood-risk indicator extending farmer exposure with world-volatility dependence | index | monthly | exposure plus standardized world-volatility component | derived |
