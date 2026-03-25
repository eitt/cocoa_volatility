# Dataset Search Instructions

## Purpose

Identify reliable public or official time-series datasets that connect Colombian cocoa markets, international cocoa benchmarks, European downstream price indicators, trade linkages, macro controls, and optional climate stress extensions.

## Output Required From the Search Agent

The search should produce:

- one master inventory table covering all candidate datasets
- one source-quality assessment using the priority rules below
- one short recommendation memo choosing the best series for each analytical block

## Priority Order

1. Official statistical agencies
2. Intergovernmental organizations
3. Central banks and customs authorities
4. Peer-reviewed supplementary datasets
5. Private providers only if no public alternative exists

## Exclusion Rules

Do not prioritize:

- blogs
- news articles
- dashboards without downloadable metadata
- reposts of official data
- undocumented scraped series

## Required Metadata Fields

For each dataset found, record:

- source institution
- exact dataset name
- download link
- access format
- geographic coverage
- time coverage
- frequency
- unit of measurement
- variable names
- access restrictions
- update pattern
- source type: official, intergovernmental, academic, or private

## Search Blocks

### A. Colombian Domestic Price Data

Search for:

- cocoa bean prices in Colombia
- SIPSA wholesale agricultural prices
- producer or farmgate proxies if available
- regional prices for cocoa-producing areas if available
- daily, weekly, or monthly series with the longest span possible

Capture these variables:

- date
- product name
- market or city
- price
- unit
- source institution
- methodology note

### B. International Cocoa Commodity Prices

Search for:

- ICCO cocoa price series
- World Bank Pink Sheet cocoa prices
- IMF commodity price datasets if public and documented
- other official benchmark cocoa series

Capture:

- date
- world cocoa price
- currency
- unit
- methodology

### C. European Market Prices

Search for:

- Eurostat HICP or CPI subseries for cocoa, chocolate, and confectionery
- producer prices or import prices related to cocoa-based goods
- France-specific series and EU aggregates where available

Capture:

- date
- country
- index or price
- classification code
- base year
- frequency

### D. Trade and Supply-Chain Linkages

Search for:

- Colombian cocoa and chocolate exports to Europe
- European imports from Colombia
- HS codes 1801, 1803, 1804, 1805, and 1806
- annual and monthly flows where available

Capture:

- reporter
- partner
- HS code
- year or month
- value
- quantity
- quantity unit

### E. Macroeconomic and Control Variables

Search for:

- COP/USD exchange rate
- EUR/USD and COP/EUR exchange rates
- inflation indices for deflation
- freight or shipping proxies if defensible
- fertilizer or energy price controls if used

### F. Climate and Agronomic Extensions

Search for data that can support robustness analysis related to water stress, biomass density, irrigation, and drainage.

Required extension workflow:

1. Identify the top five cocoa-producing Colombian departments using the most recent official production statistics available.
2. For those five departments, identify representative coordinates or centroids that can be used with NASA POWER.
3. Download or document NASA POWER daily or monthly time series for variables used or motivated by the 2025 Ecological Informatics paper at `https://doi.org/10.1016/j.ecoinf.2025.103262`.
4. Prioritize variables such as precipitation, temperature, relative humidity, irradiance, and wind speed if they are consistent with the paper and available from NASA POWER.

Possible analytical uses:

- climate shock controls
- rainfall anomalies
- drought or water-stress proxies
- discussion of productive vulnerability

## Search Notes

- Prefer downloadable files, APIs, or clearly documented query systems.
- Record any registration or API-key requirements.
- If multiple candidate series exist, prefer the one with stronger metadata, longer coverage, and more stable updates.
- Do not force the 2025 biomass-density paper into the core price-transmission model unless spatial and temporal alignment is demonstrated.
