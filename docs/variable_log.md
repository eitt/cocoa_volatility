# Variable Log

| canonical_name | description | unit | frequency | transform_notes | likely_source |
| --- | --- | --- | --- | --- | --- |
| colombia_cocoa_price_cop_kg | Colombian cocoa bean market price proxy | COP/kg | daily-weekly-monthly | aggregate to monthly mean or median | SIPSA / DANE |
| world_cocoa_price_usd_mt | International cocoa benchmark price | USD/metric ton | daily-monthly | convert to monthly average | ICCO / World Bank |
| eu_hicp_chocolate_index | EU downstream chocolate or cocoa consumer price index | index | monthly | use log level and log difference | Eurostat |
| colombia_exports_cocoa_usd | Colombian cocoa exports to Europe | USD | annual-monthly | aggregate by HS code and partner | UN Comtrade |
| cop_usd_exchange_rate | Colombian peso to US dollar rate | COP/USD | daily-monthly | monthly average | central bank source |
| colombia_cpi_index | Colombian CPI for deflation | index | monthly | set base year before deflation | national statistical source |
| nasa_power_precipitation | NASA POWER precipitation measure | mm/day or monthly aggregate | daily-monthly | derive anomalies if needed | NASA POWER |
