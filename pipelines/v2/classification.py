"""Event classification logic for the v2 disaster pipeline."""

from __future__ import annotations

import re

import pandas as pd

from pipelines.v2.translation import normalize_spanish_text


HYDROMETEOROLOGICAL_TYPES = {
    "Floods",
    "Flood",
    "Flash flood",
    "Torrential flash flood",
    "Thunderstorms",
    "Hailstorm",
    "Windstorm",
    "Overflow flood",
    "Frost",
}
GEOPHYSICAL_TYPES = {
    "Earthquake",
    "Earthquake tremor",
    "Landslides",
    "Mass movement",
    "Rockfall",
    "Erosion",
}
INFRASTRUCTURE_SERVICE_TYPES = {
    "Road closure",
    "Supply shortage",
    "Public emergency",
}
TECHNOLOGICAL_TYPES = {
    "Mine collapse",
    "Mine explosion",
    "Vehicle accident",
    "Mining accident",
    "Oil spill",
    "Explosion",
    "Gas leak",
    "Structural fire",
    "Structural collapse",
}


def detect_earthquake_events(dataframe: pd.DataFrame, search_fields: list[str], earthquake_terms: list[str]) -> pd.DataFrame:
    """Flag earthquake-related events using Spanish matching across multiple fields."""
    pattern = re.compile("|".join(re.escape(normalize_spanish_text(term)) for term in earthquake_terms if term), re.IGNORECASE)
    classified = dataframe.copy()

    detection_sources: list[str] = []
    detection_flags: list[bool] = []

    for _, row in classified.iterrows():
        matched_fields: list[str] = []
        for field in search_fields:
            raw_value = row.get(field, pd.NA)
            normalized = normalize_spanish_text(raw_value)
            if normalized and pattern.search(normalized):
                matched_fields.append(field.replace("_es", ""))
        detection_flags.append(bool(matched_fields))
        detection_sources.append(", ".join(matched_fields))

    classified["earthquake_detected"] = detection_flags
    classified["earthquake_detection_sources"] = detection_sources
    return classified


def classify_hazard_domain(event_type_en: str, probable_cause_en: str, earthquake_detected: bool) -> tuple[str, str]:
    """Assign a semantic hazard-domain label."""
    event_type = event_type_en or ""
    cause = probable_cause_en or ""

    if earthquake_detected or event_type in GEOPHYSICAL_TYPES:
        return "geophysical", "Geophysical"
    if event_type in HYDROMETEOROLOGICAL_TYPES or cause in {"Heavy rainfall", "El Nino phenomenon", "Drought", "Dry season"}:
        return "hydrometeorological", "Hydrometeorological"
    if event_type in INFRASTRUCTURE_SERVICE_TYPES:
        return "infrastructure_service", "Infrastructure and service disruption"
    if event_type in TECHNOLOGICAL_TYPES or cause in {"Terrorist attack", "Vehicle accident", "COVID-19"}:
        return "technological_anthropogenic", "Technological and anthropogenic"
    return "other", "Other or unclassified"


def classify_impact_profile(row: pd.Series) -> str:
    """Describe the dominant recorded impact category without creating a composite index."""
    human_impact = float(row.get("human_impact_total", 0.0) or 0.0) if pd.notna(row.get("human_impact_total", 0.0)) else 0.0
    housing_impact = float(row.get("housing_impact_total", 0.0) or 0.0) if pd.notna(row.get("housing_impact_total", 0.0)) else 0.0
    infrastructure_impact = (
        float(row.get("infrastructure_impact_total", 0.0) or 0.0) if pd.notna(row.get("infrastructure_impact_total", 0.0)) else 0.0
    )
    affected_hectares = float(row.get("affected_hectares", 0.0) or 0.0) if pd.notna(row.get("affected_hectares", 0.0)) else 0.0

    if human_impact > 0:
        return "Human impact recorded"
    if housing_impact > 0:
        return "Housing damage recorded"
    if infrastructure_impact > 0:
        return "Infrastructure damage recorded"
    if affected_hectares > 0:
        return "Agricultural or land impact recorded"
    return "No quantified impact recorded"


def build_semantic_event_model(
    dataframe: pd.DataFrame,
    search_fields: list[str],
    earthquake_terms: list[str],
) -> pd.DataFrame:
    """Add earthquake flags and semantic hazard classes."""
    classified = detect_earthquake_events(dataframe, search_fields=search_fields, earthquake_terms=earthquake_terms)

    hazard_keys: list[str] = []
    hazard_labels: list[str] = []
    impact_profiles: list[str] = []
    for _, row in classified.iterrows():
        hazard_key, hazard_label = classify_hazard_domain(
            event_type_en=row.get("event_type_en", "Not reported"),
            probable_cause_en=row.get("probable_cause_en", "Not reported"),
            earthquake_detected=bool(row.get("earthquake_detected", False)),
        )
        hazard_keys.append(hazard_key)
        hazard_labels.append(hazard_label)
        impact_profiles.append(classify_impact_profile(row))

    classified["hazard_domain_key"] = hazard_keys
    classified["hazard_domain_en"] = hazard_labels
    classified["impact_profile_en"] = impact_profiles
    return classified
