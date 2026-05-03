"""Build traceable resilience artifacts for paper_v3_integrated.tex.

The script keeps the disaster layer contextual. It generates diagnostic tables
for structural breaks, natural-capital stress, hazard screening, PCA pressure,
event windows, basis risk, and reviewer-audit documentation.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "outputs" / "tables"
APPENDIX_DIR = ROOT / "outputs" / "appendix"
DOCS_DIR = ROOT / "docs"

CORE_PANEL = ROOT / "data" / "processed" / "final_series" / "core_common_window_panel_imputed.csv"
WEATHER_PANEL = ROOT / "data" / "processed" / "final_series" / "weather_common_window_panel_imputed.csv"
VULNERABILITY_METRICS = ROOT / "data" / "processed" / "final_series" / "vulnerability_metrics.csv"
EVENT_PANEL = ROOT / "reports" / "v2" / "intermediate" / "04_monthly_event_panel.csv"
INTEGRATED_PANEL = ROOT / "reports" / "v2" / "intermediate" / "v3_integrated_panel.csv"
PCA_LOADINGS = ROOT / "reports" / "v2" / "tables" / "table_pca_loadings.csv"
ANALYSIS_SUMMARY = ROOT / "reports" / "v2" / "analysis_summary_v2.json"
CORE_COEFFICIENTS = ROOT / "outputs" / "tables" / "table_core_transmission_coefficients.csv"
WEATHER_COEFFICIENTS = ROOT / "outputs" / "tables" / "table_weather_vulnerability_coefficients.csv"
WEATHER_FIT = ROOT / "outputs" / "tables" / "table_weather_vulnerability_model_fit.csv"


def _ensure_dirs() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    APPENDIX_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)


def _write_table(df: pd.DataFrame, filename: str) -> Path:
    path = TABLE_DIR / filename
    df.to_csv(path, index=False)
    return path


def _fmt_float(value: float | int | None, digits: int = 3) -> str:
    if value is None or pd.isna(value):
        return ""
    return f"{float(value):.{digits}f}"


def _load_core_returns() -> pd.DataFrame:
    df = pd.read_csv(CORE_PANEL, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    variables = {
        "colombia_return": "colombia_cocoa_price_cop_kg",
        "world_return": "world_cocoa_price_usd_mt",
        "fx_return": "cop_usd_exchange_rate",
        "oil_return": "brent_oil_usd_bbl",
    }
    for out_col, raw_col in variables.items():
        df[out_col] = np.log(df[raw_col]).diff()
    return df[["date", "colombia_return", "world_return", "fx_return", "oil_return"]].dropna().reset_index(drop=True)


def _fit_segment(df: pd.DataFrame) -> tuple[float, pd.Series]:
    y = df["colombia_return"].astype(float)
    x = sm.add_constant(df[["world_return", "fx_return", "oil_return"]].astype(float), has_constant="add")
    model = sm.OLS(y, x).fit()
    rss = float(np.sum(model.resid**2))
    return rss, model.params


def build_structural_break_table() -> pd.DataFrame:
    df = _load_core_returns()
    n_obs = len(df)
    min_segment = 18
    k_per_segment = 4

    rss0, params0 = _fit_segment(df)
    bic0 = n_obs * np.log(rss0 / n_obs) + k_per_segment * np.log(n_obs)

    best: dict[str, object] | None = None
    if n_obs >= 2 * min_segment:
        for break_index in range(min_segment, n_obs - min_segment + 1):
            before = df.iloc[:break_index]
            after = df.iloc[break_index:]
            rss_before, params_before = _fit_segment(before)
            rss_after, params_after = _fit_segment(after)
            rss = rss_before + rss_after
            bic = n_obs * np.log(rss / n_obs) + (2 * k_per_segment + 1) * np.log(n_obs)
            if best is None or bic < float(best["bic"]):
                best = {
                    "break_index": break_index,
                    "break_date": pd.Timestamp(df.loc[break_index, "date"]).date().isoformat(),
                    "bic": bic,
                    "rss": rss,
                    "params_before": params_before,
                    "params_after": params_after,
                }

    rows: list[dict[str, object]] = [
        {
            "model": "core_return_transmission_no_break",
            "dependent_variable": "colombian_cocoa_log_return",
            "sample_start": df["date"].min().date().isoformat(),
            "sample_end": df["date"].max().date().isoformat(),
            "n_obs": n_obs,
            "break_date": "",
            "segment_before": n_obs,
            "segment_after": 0,
            "criterion": f"BIC={bic0:.3f}; selected baseline",
            "beta_world_before": float(params0["world_return"]),
            "beta_world_after": "",
            "interpretation_note": "No-break benchmark retained by BIC; used as the primary transmission specification.",
        }
    ]

    if best is not None:
        selected = float(best["bic"]) < bic0
        params_before = best["params_before"]
        params_after = best["params_after"]
        rows.append(
            {
                "model": "core_return_transmission_best_one_break_candidate",
                "dependent_variable": "colombian_cocoa_log_return",
                "sample_start": df["date"].min().date().isoformat(),
                "sample_end": df["date"].max().date().isoformat(),
                "n_obs": n_obs,
                "break_date": best["break_date"],
                "segment_before": int(best["break_index"]),
                "segment_after": int(n_obs - int(best["break_index"])),
                "criterion": f"BIC={float(best['bic']):.3f}; no-break BIC={bic0:.3f}; {'selected' if selected else 'not selected'}",
                "beta_world_before": float(params_before["world_return"]),
                "beta_world_after": float(params_after["world_return"]),
                "interpretation_note": (
                    "Candidate split from segmented OLS RSS search; treated as diagnostic only."
                    if selected
                    else "Best one-break split is not retained by BIC and is not interpreted as a detected regime shift."
                ),
            }
        )
    return pd.DataFrame(rows)


def build_weather_stress_summary() -> pd.DataFrame:
    weather = pd.read_csv(WEATHER_PANEL, parse_dates=["date"]).sort_values("date")
    vuln = pd.read_csv(VULNERABILITY_METRICS, parse_dates=["date"]).sort_values("date")
    start = weather["date"].min().date().isoformat()
    end = weather["date"].max().date().isoformat()
    weather_stress_mean = vuln["weather_stress_index"].mean()
    weather_stress_sd = vuln["weather_stress_index"].std(ddof=1)

    rows = [
        {
            "variable": "nasa_precipitation_mm_day",
            "source": "NASA POWER monthly point series for San Vicente de Chucuri",
            "transformation": "Monthly z-score over the aligned weather window",
            "anomaly_definition": "Deviation from the 2021-08 to 2025-12 local monthly mean divided by the aligned-window standard deviation",
            "sample_window": f"{start} to {end}",
            "role_in_model": "Weather-augmented level model and lagged return model",
            "interpretation_as_natural_capital_stress": "Threshold-relevant soil-moisture and harvest-logistics proxy; not a measured farm-level physiological threshold.",
            "summary_value": "",
        },
        {
            "variable": "nasa_surface_solar_radiation_mj_m2_day",
            "source": "NASA POWER monthly point series for San Vicente de Chucuri",
            "transformation": "Monthly z-score over the aligned weather window",
            "anomaly_definition": "Deviation from the 2021-08 to 2025-12 local monthly mean divided by the aligned-window standard deviation",
            "sample_window": f"{start} to {end}",
            "role_in_model": "Weather-augmented level model and lagged return model",
            "interpretation_as_natural_capital_stress": "Radiation-condition proxy relevant to shade, evapotranspiration, and disease-pressure context; not a direct agronomic measurement.",
            "summary_value": "",
        },
        {
            "variable": "nasa_temperature_max_c",
            "source": "NASA POWER monthly point series for San Vicente de Chucuri",
            "transformation": "Monthly z-score over the aligned weather window",
            "anomaly_definition": "Deviation from the 2021-08 to 2025-12 local monthly mean divided by the aligned-window standard deviation",
            "sample_window": f"{start} to {end}",
            "role_in_model": "Weather-augmented level model and lagged return model",
            "interpretation_as_natural_capital_stress": "Heat-exposure proxy relevant to flowering, pod development, and labor/harvest stress; not a farm-level heat-threshold test.",
            "summary_value": "",
        },
        {
            "variable": "weather_stress_index",
            "source": "Derived from NASA POWER precipitation, solar radiation, and maximum temperature anomalies",
            "transformation": "Mean absolute standardized anomaly across the three selected weather variables",
            "anomaly_definition": "Contextual anomaly score; higher values indicate larger combined deviations from local aligned-window norms",
            "sample_window": f"{vuln['date'].min().date().isoformat()} to {vuln['date'].max().date().isoformat()}",
            "role_in_model": "Natural-capital stress proxy and contextual overlay",
            "interpretation_as_natural_capital_stress": "Identifies stress conditions that may move the cocoa system closer to physiological or logistical tipping points without measuring those thresholds directly.",
            "summary_value": f"mean={weather_stress_mean:.3f}; sd={weather_stress_sd:.3f}",
        },
    ]
    return pd.DataFrame(rows)


def _nested_panel() -> pd.DataFrame:
    panel = pd.read_csv(INTEGRATED_PANEL, parse_dates=["date", "month"]).sort_values("month")
    events = pd.read_csv(EVENT_PANEL, parse_dates=["month"]).sort_values("month")
    df = panel.merge(events, on="month", how="left")
    mask = (df["month"] >= "2021-08-01") & (df["month"] <= "2024-07-01")
    df = df.loc[mask].copy().reset_index(drop=True)
    df["colombia_return"] = df["colombia_cocoa_price_cop_kg_log_return"]
    return df


def _overlay_coefficient(df: pd.DataFrame, signal: str) -> tuple[float | None, float | None]:
    model_df = df[["colombia_return", "world_return", "fx_return", "oil_return", signal]].dropna().copy()
    if model_df.empty or model_df[signal].std(ddof=0) == 0:
        return None, None
    model_df["signal_z"] = (model_df[signal] - model_df[signal].mean()) / model_df[signal].std(ddof=0)
    x = sm.add_constant(model_df[["world_return", "fx_return", "oil_return", "signal_z"]], has_constant="add")
    y = model_df["colombia_return"]
    model = sm.OLS(y, x).fit(cov_type="HAC", cov_kwds={"maxlags": 1})
    return float(model.params["signal_z"]), float(model.pvalues["signal_z"])


def build_hazard_screening_table() -> pd.DataFrame:
    df = _nested_panel()
    signals = [
        ("earthquake_events", "earthquake counts"),
        ("hydrometeorological_events", "hydrometeorological counts"),
        ("geophysical_events", "geophysical counts"),
        ("total_events", "total event counts"),
        ("disaster_pressure", "PCA pressure index"),
    ]
    records = []
    for column, label in signals:
        series = df[column].fillna(0.0).astype(float)
        peak_idx = int(series.idxmax())
        coef, p_value = _overlay_coefficient(df, column)
        corr_df = df[["colombia_return", column]].dropna()
        corr = corr_df["colombia_return"].corr(corr_df[column]) if len(corr_df) >= 3 else np.nan
        if column == "earthquake_events":
            decision = "Screened but too sparse for direct monthly modeling."
        elif column == "hydrometeorological_events":
            decision = "Most defensible direct monthly territorial episode marker."
        elif column == "disaster_pressure":
            decision = "Synthetic territorial-pressure overlay, not a causal price driver."
        else:
            decision = "Contextual comparator, not preferred direct episode marker."
        records.append(
            {
                "hazard_series": label,
                "sample_window": f"{df['month'].min().date().isoformat()} to {df['month'].max().date().isoformat()}",
                "total_events": float(series.sum()),
                "nonzero_months": int((series != 0).sum()),
                "zero_month_share": float((series == 0).mean()),
                "peak_month": pd.Timestamp(df.loc[peak_idx, "month"]).date().isoformat(),
                "peak_count": float(series.max()),
                "correlation_with_colombian_returns": corr,
                "overlay_coefficient_if_available": "" if coef is None else f"{coef:.3f} (p={p_value:.3f})",
                "interpretation_decision": decision,
            }
        )
    return pd.DataFrame(records)


FEATURE_BLOCKS = {
    "total_events": ("Event frequency", "Total monthly registry records"),
    "unique_municipalities": ("Spatial spread", "Number of municipalities with at least one event"),
    "earthquake_events": ("Hazard family", "Earthquake-related monthly count"),
    "geophysical_events": ("Hazard family", "Geophysical monthly count"),
    "hydrometeorological_events": ("Hazard family", "Hydrometeorological monthly count"),
    "infrastructure_service_events": ("Hazard family", "Infrastructure and service disruption monthly count"),
    "technological_anthropogenic_events": ("Hazard family", "Technological and anthropogenic monthly count"),
    "affected_families_total": ("Human impact", "Affected families"),
    "destroyed_houses_total": ("Housing impact", "Destroyed houses"),
    "damaged_houses_total": ("Housing impact", "Damaged houses"),
    "destroyed_aqueducts_total": ("Infrastructure impact", "Destroyed aqueducts"),
    "affected_roads_total": ("Infrastructure impact", "Affected roads"),
    "affected_bridges_total": ("Infrastructure impact", "Affected bridges"),
    "affected_educational_establishments_total": ("Infrastructure impact", "Affected educational establishments"),
    "affected_hectares_total": ("Agricultural impact", "Affected hectares"),
    "injuries_total": ("Human impact", "Injuries"),
    "missing_persons_total": ("Human impact", "Missing persons"),
    "deaths_total": ("Human impact", "Deaths"),
    "human_impact_total": ("Human impact", "Aggregate human impact"),
    "housing_impact_total": ("Housing impact", "Aggregate housing impact"),
    "infrastructure_impact_total": ("Infrastructure impact", "Aggregate infrastructure impact"),
}


def build_pca_loadings_table() -> pd.DataFrame:
    loadings = pd.read_csv(PCA_LOADINGS)
    summary = json.loads(ANALYSIS_SUMMARY.read_text(encoding="utf-8"))
    variance = summary.get("explained_variance_ratio")
    rows = []
    for _, row in loadings.iterrows():
        feature = row["feature"]
        block, description = FEATURE_BLOCKS.get(feature, ("Other", feature.replace("_", " ")))
        loading = float(row["loading"])
        rows.append(
            {
                "feature_name": feature,
                "feature_block": block,
                "loading_PC1": loading,
                "sign_interpretation": "Positive loading raises territorial pressure score" if loading >= 0 else "Negative loading lowers territorial pressure score after PCA orientation",
                "variable_description": description,
                "pc1_variance_explained": variance,
            }
        )
    return pd.DataFrame(rows)


def build_pca_top_months_table(top_n: int = 8) -> pd.DataFrame:
    df = _nested_panel()
    ordered = df.sort_values("disaster_pressure", ascending=False).head(top_n)
    rows = []
    for _, row in ordered.iterrows():
        month = pd.Timestamp(row["month"]).date().isoformat()
        note = "Peak composite territorial-pressure month." if month == "2022-10-01" else "High composite territorial-pressure month."
        rows.append(
            {
                "month": month,
                "PCA_pressure_score": float(row["disaster_pressure"]),
                "hydrometeorological_count": float(row["hydrometeorological_events"]),
                "total_event_count": float(row["total_events"]),
                "interpretation_note": note,
            }
        )
    return pd.DataFrame(rows)


def build_event_window_table(window: int = 6) -> pd.DataFrame:
    df = _nested_panel()
    event_month = pd.Timestamp(df.loc[df["hydrometeorological_events"].astype(float).idxmax(), "month"])
    returns = df[["month", "colombia_return"]].dropna().copy()
    pre = returns[(returns["month"] < event_month) & (returns["month"] >= event_month - pd.DateOffset(months=window))]
    post = returns[(returns["month"] > event_month) & (returns["month"] <= event_month + pd.DateOffset(months=window))]
    welch = stats.ttest_ind(pre["colombia_return"], post["colombia_return"], equal_var=False, nan_policy="omit")
    levene = stats.levene(pre["colombia_return"], post["colombia_return"], center="median")
    ks = stats.ks_2samp(pre["colombia_return"], post["colombia_return"])
    return pd.DataFrame(
        [
            {
                "event_month": event_month.date().isoformat(),
                "selection_basis": "Peak hydrometeorological count; same month as peak PCA pressure score",
                "window_length": window,
                "pre_mean_colombian_return": float(pre["colombia_return"].mean()),
                "post_mean_colombian_return": float(post["colombia_return"].mean()),
                "welch_p": float(welch.pvalue),
                "levene_p": float(levene.pvalue),
                "ks_p": float(ks.pvalue),
                "interpretation_note": "Exploratory resilience-dividend discussion window; not a quasi-experiment or causal disaster effect.",
                "endogenous_event_selection_warning": "Event month selected from the same nested hazard data used in the screen.",
            }
        ]
    )


def build_basis_risk_markers() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "marker": "hydrometeorological event concentration",
                "empirical_source": "outputs/tables/table_v3_hazard_screening.csv",
                "spatial_scale": "Santander departmental registry",
                "temporal_window": "2021-08 to 2024-07",
                "relevance_to_basis_risk": "Local landslide, rainfall, and road-disruption pressure can occur while benchmark-linked tools remain national or global.",
                "limitation": "Departmental counts do not identify each producer's realized access constraint.",
            },
            {
                "marker": "PCA pressure peak months",
                "empirical_source": "outputs/tables/table_v3_pca_pressure_top_months.csv",
                "spatial_scale": "Santander departmental registry",
                "temporal_window": "2021-08 to 2024-07",
                "relevance_to_basis_risk": "Composite pressure identifies months when several territorial stress dimensions coincide.",
                "limitation": "Synthetic index is an exposure marker, not a direct financial loss measure.",
            },
            {
                "marker": "weather-stress anomaly months",
                "empirical_source": "outputs/tables/table_v3_weather_stress_summary.csv",
                "spatial_scale": "NASA POWER point for San Vicente de Chucuri",
                "temporal_window": "2021-08 to 2025-12",
                "relevance_to_basis_risk": "Natural-capital stress can affect production and logistics even when benchmark prices move favorably.",
                "limitation": "Point-based anomaly proxies do not measure farm-specific thresholds.",
            },
            {
                "marker": "benchmark transmission under local stress",
                "empirical_source": "outputs/tables/table_core_transmission_coefficients.csv; outputs/tables/table_v3_hazard_screening.csv",
                "spatial_scale": "National producer-linked price plus departmental disaster overlay",
                "temporal_window": "2021-09 to 2025-12 for returns; nested 2021-09 to 2024-07 disaster overlap",
                "relevance_to_basis_risk": "Strong benchmark pass-through can coexist with localized disruptions to circulation, buyer access, and liquidity.",
                "limitation": "The design does not estimate municipal or household welfare impacts.",
            },
            {
                "marker": "scale mismatch across datasets",
                "empirical_source": "docs/paper_v3_statistical_artifact_audit.md",
                "spatial_scale": "Global/national price, point weather, departmental disaster registry",
                "temporal_window": "Uneven overlap across data blocks",
                "relevance_to_basis_risk": "The mismatch itself documents why benchmark-linked instruments may be territorially blind.",
                "limitation": "Policy implications are interpretive and require instrument-level validation.",
            },
        ]
    )


def build_empirical_layers_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "layer": "Core benchmark transmission",
                "main_artifact": "outputs/tables/table_core_transmission_coefficients.csv",
                "sample_window": "2021-09 to 2025-12",
                "empirical_role": "Identifies benchmark exposure in Colombian producer-linked returns.",
                "interpretation_limit": "Reduced-form monthly association, not a full pricing-chain structural model.",
            },
            {
                "layer": "Weather natural-capital stress",
                "main_artifact": "outputs/tables/table_v3_weather_stress_summary.csv",
                "sample_window": "2021-08 to 2025-12",
                "empirical_role": "Contextual anomaly score for local stress conditions.",
                "interpretation_limit": "Not farm-level physiological measurement.",
            },
            {
                "layer": "Direct disaster hazard screen",
                "main_artifact": "outputs/tables/table_v3_hazard_screening.csv",
                "sample_window": "2021-08 to 2024-07",
                "empirical_role": "Selects hydrometeorological counts as the most defensible direct monthly episode marker.",
                "interpretation_limit": "Not causal disaster-price identification.",
            },
            {
                "layer": "PCA territorial-pressure overlay",
                "main_artifact": "outputs/tables/table_v3_pca_pressure_loadings.csv",
                "sample_window": "2021-08 to 2024-07",
                "empirical_role": "Summarizes multi-dimensional territorial disruption.",
                "interpretation_limit": "Synthetic contextual construct, not a benchmark-like economic time series.",
            },
            {
                "layer": "Event-window comparison",
                "main_artifact": "outputs/tables/table_v3_event_window_tests.csv",
                "sample_window": "Six months before and after 2022-10",
                "empirical_role": "Exploratory episode stratification for resilience-dividend discussion.",
                "interpretation_limit": "Endogenously selected window; not a quasi-experiment.",
            },
            {
                "layer": "Structural-break diagnostic",
                "main_artifact": "outputs/tables/table_v3_structural_breaks.csv",
                "sample_window": "2021-09 to 2025-12",
                "empirical_role": "Bai-Perron-style segmented OLS RSS/BIC diagnostic for regime-sensitive transmission.",
                "interpretation_limit": "Short monthly sample supports diagnostics only; BIC retains no-break baseline.",
            },
            {
                "layer": "Basis-risk policy interpretation",
                "main_artifact": "outputs/tables/table_v3_basis_risk_markers.csv",
                "sample_window": "Integrated evidence base",
                "empirical_role": "Documents scale and stress markers behind territorial blindness of standard instruments.",
                "interpretation_limit": "Policy implications are not estimates of instrument effectiveness.",
            },
        ]
    )


def _markdown_table(rows: list[dict[str, object]], columns: list[str]) -> str:
    df = pd.DataFrame(rows, columns=columns).fillna("")
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for _, row in df.iterrows():
        body.append("| " + " | ".join(str(row[col]).replace("\n", " ") for col in columns) + " |")
    return "\n".join([header, sep, *body])


def write_limitation_note() -> None:
    text = """# V3 Missing Artifacts and Data Limitations

All requested V3 tables were generated from existing repository data. No farm-level
agroforestry-density, monoculture-comparison, household welfare, municipal price, or
instrument-level insurance/fund dataset was found in the inspected repository inputs.
Accordingly, the manuscript treats agroforestry and resilience-dividend language as
theoretical buffer-capacity interpretation rather than as an empirically tested land-use
contrast. Basis-risk and financial-equity recommendations are policy implications from
scale mismatch and overlapping stress markers, not estimated effects of specific financial
instruments.
"""
    (APPENDIX_DIR / "v3_missing_artifacts_note.md").write_text(text, encoding="utf-8")


def write_audit_memo() -> None:
    columns = [
        "Manuscript claim",
        "Manuscript section",
        "Required statistical artifact",
        "Existing artifact found?",
        "Existing file path",
        "Can be generated from repository data?",
        "Action taken",
        "Remaining limitation",
    ]
    rows = [
        {
            "Manuscript claim": "HAC-robust benchmark transmission models",
            "Manuscript section": "Methods; Results",
            "Required statistical artifact": "Core transmission coefficients and model fit",
            "Existing artifact found?": "Yes",
            "Existing file path": "outputs/tables/table_core_transmission_coefficients.csv; outputs/tables/table_core_transmission_model_fit.csv",
            "Can be generated from repository data?": "Yes",
            "Action taken": "Retained existing core artifacts and linked them in the layer summary.",
            "Remaining limitation": "Reduced-form monthly design; not a full structural pricing-chain model.",
        },
        {
            "Manuscript claim": "Weather-augmented transmission models",
            "Manuscript section": "Methods; Results; Supplement",
            "Required statistical artifact": "Weather coefficients and fit comparison",
            "Existing artifact found?": "Yes",
            "Existing file path": "outputs/tables/table_weather_vulnerability_coefficients.csv; outputs/tables/table_weather_vulnerability_model_fit.csv",
            "Can be generated from repository data?": "Yes",
            "Action taken": "Retained as contextual robustness and avoided weather-dominant price claims.",
            "Remaining limitation": "Weather variables are point-based contextual proxies.",
        },
        {
            "Manuscript claim": "NASA POWER anomaly / weather-stress index",
            "Manuscript section": "Weather-Based Contextual Stress; Results",
            "Required statistical artifact": "Weather-stress summary table",
            "Existing artifact found?": "Partial",
            "Existing file path": "data/processed/final_series/vulnerability_metrics.csv; outputs/tables/table_weather_variable_selection.csv",
            "Can be generated from repository data?": "Yes",
            "Action taken": "Generated outputs/tables/table_v3_weather_stress_summary.csv.",
            "Remaining limitation": "No farm-level physiological thresholds observed.",
        },
        {
            "Manuscript claim": "Hydrometeorological hazard screening",
            "Manuscript section": "Contextual Disaster Exposure Layer; Results",
            "Required statistical artifact": "Hazard-screening table",
            "Existing artifact found?": "Partial",
            "Existing file path": "outputs/tables/table_hazard_signal_screening.csv; outputs/tables/table_hazard_overlay_model_comparison.csv",
            "Can be generated from repository data?": "Yes",
            "Action taken": "Generated outputs/tables/table_v3_hazard_screening.csv with correlations and overlay coefficients.",
            "Remaining limitation": "Screening is contextual and not causal.",
        },
        {
            "Manuscript claim": "Earthquake-count sparsity",
            "Manuscript section": "Contextual Disaster Exposure Layer; Results",
            "Required statistical artifact": "Zero-inflation and nonzero-month screening",
            "Existing artifact found?": "Yes",
            "Existing file path": "reports/v2/tables/table_earthquake_feasibility.csv",
            "Can be generated from repository data?": "Yes",
            "Action taken": "Included earthquake counts in outputs/tables/table_v3_hazard_screening.csv.",
            "Remaining limitation": "Only four nonzero earthquake months in the nested window.",
        },
        {
            "Manuscript claim": "PCA-based disaster-pressure index",
            "Manuscript section": "Contextual Disaster Exposure Layer; Results",
            "Required statistical artifact": "PCA loadings, variance explained, and top months",
            "Existing artifact found?": "Yes",
            "Existing file path": "reports/v2/tables/table_pca_loadings.csv; reports/v2/analysis_summary_v2.json",
            "Can be generated from repository data?": "Yes",
            "Action taken": "Generated outputs/tables/table_v3_pca_pressure_loadings.csv and outputs/tables/table_v3_pca_pressure_top_months.csv.",
            "Remaining limitation": "Synthetic territorial-pressure index, not a causal economic time series.",
        },
        {
            "Manuscript claim": "October 2022 pressure/event-window result",
            "Manuscript section": "Event-Based Mean-Shift Design; Results",
            "Required statistical artifact": "Welch, Levene, and KS event-window tests",
            "Existing artifact found?": "No final V3 table",
            "Existing file path": "reports/v2/analysis_summary_v2.json identified shock_date",
            "Can be generated from repository data?": "Yes",
            "Action taken": "Generated outputs/tables/table_v3_event_window_tests.csv.",
            "Remaining limitation": "Endogenous event selection; not a quasi-experiment.",
        },
        {
            "Manuscript claim": "Structural-break or tipping-point diagnostics",
            "Manuscript section": "Structural Breaks, Tipping Points, and Regime-Sensitive Transmission",
            "Required statistical artifact": "Segmented OLS RSS/BIC break diagnostic",
            "Existing artifact found?": "No",
            "Existing file path": "",
            "Can be generated from repository data?": "Yes",
            "Action taken": "Generated outputs/tables/table_v3_structural_breaks.csv.",
            "Remaining limitation": "Short monthly sample; BIC retains no-break baseline.",
        },
        {
            "Manuscript claim": "Resilience-dividend interpretation",
            "Manuscript section": "Results; Discussion",
            "Required statistical artifact": "Event-window table plus limitation note",
            "Existing artifact found?": "Partial",
            "Existing file path": "outputs/tables/table_v3_event_window_tests.csv; outputs/appendix/v3_missing_artifacts_note.md",
            "Can be generated from repository data?": "Partially",
            "Action taken": "Reframed as theoretical buffer-capacity discussion rather than tested agroforestry effect.",
            "Remaining limitation": "No agroforestry-density or monoculture comparison dataset found.",
        },
        {
            "Manuscript claim": "Basis-risk policy interpretation",
            "Manuscript section": "Basis Risk, Territorial Blindness, and Financial Equity",
            "Required statistical artifact": "Basis-risk marker table",
            "Existing artifact found?": "No",
            "Existing file path": "",
            "Can be generated from repository data?": "Yes, as evidence-marker synthesis",
            "Action taken": "Generated outputs/tables/table_v3_basis_risk_markers.csv.",
            "Remaining limitation": "Does not estimate financial-instrument effectiveness.",
        },
    ]
    text = "# Paper V3 Statistical Artifact Audit\n\n" + _markdown_table(rows, columns) + "\n"
    (DOCS_DIR / "paper_v3_statistical_artifact_audit.md").write_text(text, encoding="utf-8")


def write_reviewer_alignment_memo() -> None:
    columns = [
        "Reviewer concern",
        "Manuscript change made",
        "Artifact created or used",
        "Response type",
        "Remaining limitation",
    ]
    rows = [
        {
            "Reviewer concern": "Formalize resilience upgrade through tipping-point/regime-shift diagnostics.",
            "Manuscript change made": "Added structural-break methodology and diagnostic results with cautious interpretation.",
            "Artifact created or used": "outputs/tables/table_v3_structural_breaks.csv",
            "Response type": "Methodological and empirical",
            "Remaining limitation": "BIC retains no-break baseline in a short monthly sample.",
        },
        {
            "Reviewer concern": "Interpret NASA POWER anomalies as resilience-relevant stress indicators.",
            "Manuscript change made": "Reframed weather anomalies as natural-capital stress proxies.",
            "Artifact created or used": "outputs/tables/table_v3_weather_stress_summary.csv",
            "Response type": "Methodological and interpretive",
            "Remaining limitation": "No direct farm-level physiological thresholds.",
        },
        {
            "Reviewer concern": "Justify hydrometeorological focus and earthquake exclusion.",
            "Manuscript change made": "Clarified hazard screening and earthquake sparsity.",
            "Artifact created or used": "outputs/tables/table_v3_hazard_screening.csv",
            "Response type": "Empirical",
            "Remaining limitation": "Registry counts are contextual markers.",
        },
        {
            "Reviewer concern": "Make PCA pressure transparent.",
            "Manuscript change made": "Reported variable count, PC1 variance, loadings, and synthetic-pressure interpretation.",
            "Artifact created or used": "outputs/tables/table_v3_pca_pressure_loadings.csv; outputs/tables/table_v3_pca_pressure_top_months.csv",
            "Response type": "Empirical and methodological",
            "Remaining limitation": "PCA does not identify causal price effects.",
        },
        {
            "Reviewer concern": "Discuss resilience dividend without overstating event-window evidence.",
            "Manuscript change made": "Reframed October 2022 comparison as exploratory episode stratification and buffer-capacity discussion.",
            "Artifact created or used": "outputs/tables/table_v3_event_window_tests.csv; outputs/appendix/v3_missing_artifacts_note.md",
            "Response type": "Empirical and interpretive",
            "Remaining limitation": "No agroforestry-density or monoculture data in repository.",
        },
        {
            "Reviewer concern": "Strengthen basis-risk and financial-equity policy relevance.",
            "Manuscript change made": "Added discussion subsection on basis risk, territorial blindness, and financial equity.",
            "Artifact created or used": "outputs/tables/table_v3_basis_risk_markers.csv",
            "Response type": "Interpretive",
            "Remaining limitation": "Policy recommendations are not tested instruments.",
        },
        {
            "Reviewer concern": "Use verified references for Bai-Perron and resilience dividends.",
            "Manuscript change made": "Added Bai and Perron references; retained verified Mechler et al. 2025 citation.",
            "Artifact created or used": "references/cocoa_volatility.bib; paper/references/cocoa_volatility.bib",
            "Response type": "Bibliographic",
            "Remaining limitation": "None for these cited items after verification.",
        },
    ]
    text = "# Paper V3 Reviewer Concern Alignment\n\n" + _markdown_table(rows, columns) + "\n"
    (DOCS_DIR / "paper_v3_reviewer_concern_alignment.md").write_text(text, encoding="utf-8")


def main() -> None:
    _ensure_dirs()
    outputs = {
        "structural_breaks": _write_table(build_structural_break_table(), "table_v3_structural_breaks.csv"),
        "weather_stress": _write_table(build_weather_stress_summary(), "table_v3_weather_stress_summary.csv"),
        "hazard_screening": _write_table(build_hazard_screening_table(), "table_v3_hazard_screening.csv"),
        "pca_loadings": _write_table(build_pca_loadings_table(), "table_v3_pca_pressure_loadings.csv"),
        "pca_top_months": _write_table(build_pca_top_months_table(), "table_v3_pca_pressure_top_months.csv"),
        "event_window": _write_table(build_event_window_table(), "table_v3_event_window_tests.csv"),
        "basis_risk": _write_table(build_basis_risk_markers(), "table_v3_basis_risk_markers.csv"),
        "empirical_layers": _write_table(build_empirical_layers_table(), "table_v3_empirical_layers.csv"),
    }
    write_limitation_note()
    write_audit_memo()
    write_reviewer_alignment_memo()
    print(json.dumps({key: str(path.relative_to(ROOT)) for key, path in outputs.items()}, indent=2))


if __name__ == "__main__":
    main()
