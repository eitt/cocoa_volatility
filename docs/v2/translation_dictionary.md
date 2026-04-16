# Translation Dictionary for v2 Disaster Analytics

The v2 pipeline uses `translation/es_en_dictionary.yaml` as a reproducible Spanish-to-English translation layer for all categorical variables that enter the analytical workflow. The dictionary is applied before event classification, monthly aggregation, and report generation, which means all downstream analytics operate on English-standardized categorical fields while the original Spanish source fields remain preserved in the exported datasets.

## Dictionary Structure

Each entry is keyed by the observed Spanish term and stores a normalized form plus an English rendering. The current schema is:

```yaml
"sismo":
  normalized_spanish_term: "sismo"
  english_translation: "Earthquake"
  context: "event_type"
  notes: "Primary earthquake label."
```

The fields have the following meanings:

- `normalized_spanish_term`: accent-stripped, lowercase, whitespace-collapsed version used for matching.
- `english_translation`: the canonical English output used in `*_en` columns.
- `context`: semantic field where the rule is intended to apply, such as `event_type`, `probable_cause`, or `impact_area`.
- `notes`: optional explanation, especially for registry-specific abbreviations, misspellings, or reporting conventions.

## Translation Rules

The translation system follows four ordered rules.

First, the pipeline performs exact matching on normalized values. This is the preferred path for event types, status fields, and frequently repeated categorical labels such as `ATENDIDO`, `SISMO`, `INUNDACIONES`, and `URBANO Y RURAL`.

Second, when an exact phrase is unavailable, the pipeline applies token-aware translation using reusable dictionary terms. This is mainly used for institutional strings such as `CMGRD DE CHARTA`, which becomes `Municipal Disaster Risk Management Council of Charta`.

Third, proper nouns such as municipality names are standardized rather than literally translated. `BUCARAMANGA` becomes `Bucaramanga`, and `SAN VICENTE DE CHUCURÍ` remains the same place name in title case. This is intentional because place names are identifiers, not descriptive common nouns.

Fourth, if a value is still unmatched after the previous steps, the pipeline preserves the cleaned source text in standardized title case and records the strategy in the translation audit table. This prevents silent loss of information while keeping the workflow reproducible.

## Normalization Logic

Normalization is deterministic and is applied before dictionary lookup. The pipeline:

1. Converts text to lowercase.
2. Removes diacritics such as `í`, `ó`, and `ñ` for matching purposes.
3. Collapses duplicated whitespace.
4. Removes non-informative punctuation while preserving the alphanumeric content needed for abbreviations and locality labels.
5. Maps generic missing-value markers such as `N/A` to `Not reported`.

This approach ensures that variants such as `movimiento sísmico`, `movimiento sismico`, and strings with duplicated spaces resolve to the same normalized representation.

## Ambiguity Handling

Not every registry value should be translated literally. The v2 system uses the following ambiguity policy:

- Administrative acronyms are expanded when they function as institutions, for example `CMGRD`.
- Proper nouns are preserved as names.
- Misspellings are normalized when the intended meaning is unambiguous, such as `INUDACIONES` to `Floods`.
- Free-text narrative fields such as `OBSERVACIONES` are not machine-translated into English. Instead, the report narrative is generated directly in English from analytical outputs. This avoids brittle literal translation of operational field notes.

## Examples

Representative examples from the current registry include:

- `SISMO` -> `Earthquake`
- `CRECIENTE SUBITA` -> `Flash flood`
- `FENOMENO DEL NIÑO` -> `El Nino phenomenon`
- `URBANO Y RURAL` -> `Urban and rural`
- `CMGRD DE CHARTA` -> `Municipal Disaster Risk Management Council of Charta`
- `BUCARAMANGA` -> `Bucaramanga`

## Limitations

The dictionary is deliberately conservative. It is designed for deterministic standardization of repeated categorical content, not for full-sentence translation. Rare institutional strings and highly specific locality descriptions may therefore be standardized through partial token translation plus proper-noun preservation rather than through a fully idiomatic rewrite. When that happens, the output remains traceable because the original Spanish columns are kept alongside the English `*_en` columns and the translation audit table records how each value was handled.
