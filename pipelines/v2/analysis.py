"""Analytical decision tree and diagnostics for v2."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.seasonal import STL
import statsmodels.api as sm

from pipelines.v2.change_points import detect_mean_shift_pelt
from pipelines.v2.visualization import (
    plot_change_points,
    plot_hazard_domain_mix,
    plot_monthly_event_totals,
    plot_pca_loadings,
    plot_rolling_diagnostics,
    plot_stl_decomposition,
    plot_top_municipalities,
)


@dataclass
class FeasibilityResult:
    """Monthly earthquake-series feasibility diagnostics."""

    total_months: int
    nonzero_months: int
    total_events: int
    zero_share: float
    max_consecutive_zero_months: int
    is_viable: bool


def _max_consecutive_zeros(values: pd.Series) -> int:
    max_run = 0
    current_run = 0
    for value in values.tolist():
        if float(value) == 0.0:
            current_run += 1
            max_run = max(max_run, current_run)
        else:
            current_run = 0
    return max_run


def evaluate_earthquake_feasibility(monthly: pd.DataFrame, feasibility_config: dict[str, object]) -> FeasibilityResult:
    """Apply the earthquake-feasibility decision rules."""
    series = monthly["earthquake_events"].fillna(0.0)
    total_months = int(len(series))
    nonzero_months = int((series > 0).sum())
    total_events = int(series.sum())
    zero_share = float((series == 0).mean()) if total_months else 1.0
    max_consecutive_zero_months = _max_consecutive_zeros(series)

    is_viable = all(
        [
            total_months >= feasibility_config["min_total_months"],
            nonzero_months >= feasibility_config["min_nonzero_months"],
            total_events >= feasibility_config["min_total_events"],
            zero_share <= feasibility_config["max_zero_share"],
            max_consecutive_zero_months <= feasibility_config["max_consecutive_zero_months"],
        ]
    )

    return FeasibilityResult(
        total_months=total_months,
        nonzero_months=nonzero_months,
        total_events=total_events,
        zero_share=zero_share,
        max_consecutive_zero_months=max_consecutive_zero_months,
        is_viable=is_viable,
    )


def _build_decomposition(series_df: pd.DataFrame, value_column: str, stl_period: int) -> pd.DataFrame | None:
    values = series_df[value_column].astype(float)
    if len(values) < max(24, stl_period * 2) or np.allclose(values, values.iloc[0]):
        return None
    result = STL(values, period=stl_period, robust=True).fit()
    return pd.DataFrame(
        {
            "month": series_df["month"],
            "observed": values,
            "trend": result.trend,
            "seasonal": result.seasonal,
            "residual": result.resid,
        }
    )


def _build_rolling_diagnostics(series_df: pd.DataFrame, value_column: str, rolling_window_months: int) -> pd.DataFrame:
    values = series_df[value_column].astype(float)
    return pd.DataFrame(
        {
            "month": series_df["month"],
            "value": values,
            "rolling_mean": values.rolling(rolling_window_months, min_periods=1).mean(),
            "rolling_variance": values.rolling(rolling_window_months, min_periods=2).var(),
        }
    )


def _select_shock_index(values: pd.Series, change_points: list[int]) -> int:
    if not change_points:
        return int(values.argmax())

    candidate_effects = []
    for change_point in change_points:
        left = values.iloc[:change_point]
        right = values.iloc[change_point:]
        if left.empty or right.empty:
            continue
        effect = abs(right.mean() - left.mean())
        candidate_effects.append((effect, change_point))

    if not candidate_effects:
        return int(values.argmax())
    return max(candidate_effects, key=lambda item: item[0])[1]


def _build_structural_comparison(series_df: pd.DataFrame, value_column: str, shock_date: pd.Timestamp, window_months: int) -> pd.DataFrame:
    before = series_df.loc[
        (series_df["month"] < shock_date)
        & (series_df["month"] >= shock_date - pd.DateOffset(months=window_months)),
        value_column,
    ].astype(float)
    after = series_df.loc[
        (series_df["month"] >= shock_date)
        & (series_df["month"] < shock_date + pd.DateOffset(months=window_months)),
        value_column,
    ].astype(float)

    if len(before) < 2 or len(after) < 2:
        return pd.DataFrame(
            [
                {
                    "comparison": "Insufficient data",
                    "before_value": len(before),
                    "after_value": len(after),
                    "statistic": np.nan,
                    "p_value": np.nan,
                }
            ]
        )

    mean_test = stats.ttest_ind(before, after, equal_var=False, nan_policy="omit")
    variance_test = stats.levene(before, after, center="median")
    distribution_test = stats.ks_2samp(before, after, method="auto")

    return pd.DataFrame(
        [
            {
                "comparison": "Mean shift (Welch t-test)",
                "before_value": before.mean(),
                "after_value": after.mean(),
                "statistic": mean_test.statistic,
                "p_value": mean_test.pvalue,
            },
            {
                "comparison": "Variance shift (Levene test)",
                "before_value": before.var(ddof=1),
                "after_value": after.var(ddof=1),
                "statistic": variance_test.statistic,
                "p_value": variance_test.pvalue,
            },
            {
                "comparison": "Distribution shift (KS test)",
                "before_value": before.median(),
                "after_value": after.median(),
                "statistic": distribution_test.statistic,
                "p_value": distribution_test.pvalue,
            },
        ]
    )


def _series_summary(series_df: pd.DataFrame, value_column: str) -> dict[str, float]:
    values = series_df[value_column].astype(float)
    mean_value = float(values.mean())
    std_value = float(values.std(ddof=1)) if len(values) > 1 else 0.0
    coefficient_of_variation = np.nan if abs(mean_value) < 1e-9 else std_value / mean_value
    return {
        "mean": mean_value,
        "std": std_value,
        "coefficient_of_variation": coefficient_of_variation,
        "max": float(values.max()),
        "min": float(values.min()),
    }


def _run_ts_tests(series: pd.Series) -> dict[str, float]:
    """Run V1-aligned TS tests natively."""
    try:
        from statsmodels.tsa.stattools import adfuller
        from statsmodels.stats.diagnostic import het_arch
    except ImportError:
        return {"ADF_level_p": np.nan, "ADF_return_p": np.nan, "ARCH_LM_p": np.nan}

    values = series.dropna().to_numpy(dtype=float)
    adf_level = adfuller(values)[1] if len(values) > 5 else np.nan
    
    returns = np.diff(values)
    adf_return = adfuller(returns)[1] if len(returns) > 5 else np.nan
    
    try:
        arch_p = het_arch(returns)[1] if len(returns) > 10 else np.nan
    except Exception:
        arch_p = np.nan
        
    return {
        "ADF_level_p": adf_level,
        "ADF_return_p": adf_return,
        "ARCH_LM_p": arch_p
    }


def _estimate_extensions(target_df: pd.DataFrame, signal_df: pd.DataFrame, signal_column: str, rolling_window_months: int) -> dict[str, pd.DataFrame]:
    """Estimate core V1 extensions with the composite disaster indicator overlay."""
    df = target_df.copy()
    if len(df) == len(signal_df):
        df["disaster_indicator"] = signal_df[signal_column].values
    else:
        return {"return_extension": pd.DataFrame(), "volatility_extension": pd.DataFrame()}
    
    if "log_world_cocoa_price_usd_mt" in df.columns:
        df["world_return"] = df["log_world_cocoa_price_usd_mt"].diff()
        df["fx_return"] = df["log_cop_usd_exchange_rate"].diff()
        df["oil_return"] = df["log_brent_oil_usd_bbl"].diff()
        df["colombia_return"] = df["colombia_cocoa_price_cop_kg_log_return"]
    else:
        return {"return_extension": pd.DataFrame(), "volatility_extension": pd.DataFrame()}

    # 1. Return extension
    data_ret = df[["colombia_return", "world_return", "fx_return", "oil_return", "disaster_indicator"]].dropna()
    if len(data_ret) > 10:
        X_ret = sm.add_constant(data_ret[["world_return", "fx_return", "oil_return", "disaster_indicator"]])
        y_ret = data_ret["colombia_return"]
        model_ret = sm.OLS(y_ret, X_ret).fit(cov_type='HAC', cov_kwds={'maxlags': 1})
        ret_results = pd.DataFrame({
            "term": model_ret.params.index,
            "coefficient": model_ret.params.values,
            "p_value": model_ret.pvalues.values,
        })
    else:
        ret_results = pd.DataFrame()

    # 2. Volatility extension
    if "colombia_cocoa_price_cop_kg_log_return_rolling_volatility" in df.columns:
        df["world_volatility"] = df["world_return"].rolling(rolling_window_months, min_periods=2).var()
        data_vol = df[["colombia_cocoa_price_cop_kg_log_return_rolling_volatility", "world_volatility", "disaster_indicator"]].dropna()
        if len(data_vol) > 10:
            X_vol = sm.add_constant(data_vol[["world_volatility", "disaster_indicator"]])
            y_vol = data_vol["colombia_cocoa_price_cop_kg_log_return_rolling_volatility"]
            model_vol = sm.OLS(y_vol, X_vol).fit(cov_type='HAC', cov_kwds={'maxlags': 1})
            vol_results = pd.DataFrame({
                "term": model_vol.params.index,
                "coefficient": model_vol.params.values,
                "p_value": model_vol.pvalues.values,
            })
        else:
            vol_results = pd.DataFrame()
    else:
        vol_results = pd.DataFrame()
        
    return {"return_extension": ret_results, "volatility_extension": vol_results}


def _run_series_diagnostics(
    signal_df: pd.DataFrame,
    signal_column: str,
    target_df: pd.DataFrame,
    target_column: str,
    target_label: str,
    config: dict[str, object],
    figures_dir: Path,
    file_prefix: str,
) -> dict[str, object]:
    signal_values = signal_df[signal_column].astype(float)
    change_points = detect_mean_shift_pelt(signal_values.to_numpy(), penalty_multiplier=config["pelt_penalty_multiplier"])
    
    change_dates = [pd.Timestamp(signal_df.iloc[index]["month"]) for index in change_points if index < len(signal_df)]
    shock_index = _select_shock_index(signal_values, change_points)
    shock_date = pd.Timestamp(signal_df.iloc[shock_index]["month"]) if len(signal_df) else None

    # Structural testing and correlations
    ts_tests = _run_ts_tests(signal_values)
    
    target_values = target_df[target_column].astype(float)
    if len(signal_values) == len(target_values):
        correlation_with_target = pd.Series(signal_values.to_numpy()).corr(pd.Series(target_values.to_numpy()))
        
        # New rolling volatility correlation
        if "colombia_cocoa_price_cop_kg_log_return_rolling_volatility" in target_df.columns:
            target_volatility = target_df["colombia_cocoa_price_cop_kg_log_return_rolling_volatility"].astype(float)
            correlation_with_volatility = pd.Series(signal_values.to_numpy()).corr(pd.Series(target_volatility.to_numpy()))
        else:
            correlation_with_volatility = np.nan
    else:
        correlation_with_target = np.nan
        correlation_with_volatility = np.nan
        
    ts_tests["correlation_with_target"] = correlation_with_target
    ts_tests["correlation_with_volatility"] = correlation_with_volatility

    # Calculate V1 extensions
    extensions = _estimate_extensions(target_df, signal_df, signal_column, config["rolling_window_months"])

    decomposition_df = _build_decomposition(target_df, value_column=target_column, stl_period=config["stl_period"])
    rolling_df = _build_rolling_diagnostics(target_df, value_column=target_column, rolling_window_months=config["rolling_window_months"])
    structural_table = (
        _build_structural_comparison(target_df, value_column=target_column, shock_date=shock_date, window_months=config["shock_window_months"])
        if shock_date is not None
        else pd.DataFrame()
    )

    figures = {
        "rolling": str(
            plot_rolling_diagnostics(
                rolling_df,
                output_path=figures_dir / f"{file_prefix}_rolling.png",
                value_label=target_label,
            )
        ),
        "change_points": str(
            plot_change_points(
                target_df,
                output_path=figures_dir / f"{file_prefix}_change_points.png",
                value_column=target_column,
                value_label=target_label,
                change_dates=change_dates,
                shock_date=shock_date,
            )
        ),
    }

    if decomposition_df is not None:
        figures["decomposition"] = str(
            plot_stl_decomposition(
                decomposition_df,
                output_path=figures_dir / f"{file_prefix}_decomposition.png",
                title=f"STL decomposition of {target_label.lower()}",
            )
        )

    return {
        "series_df": target_df,
        "summary": _series_summary(target_df, value_column=target_column),
        "ts_tests": ts_tests,
        "model_extensions": extensions,
        "change_dates": [date.date().isoformat() for date in change_dates],
        "shock_date": shock_date.date().isoformat() if shock_date is not None else None,
        "structural_table": structural_table,
        "decomposition_df": decomposition_df,
        "rolling_df": rolling_df,
        "figures": figures,
    }


def _build_entropy_indicator(event_type_matrix: pd.DataFrame) -> pd.DataFrame:
    type_columns = [column for column in event_type_matrix.columns if column != "month"]
    active_type_count = len(type_columns)
    entropy_values = []
    for _, row in event_type_matrix.iterrows():
        counts = row[type_columns].to_numpy(dtype=float)
        total = counts.sum()
        if total <= 0 or active_type_count < 2:
            entropy_values.append(0.0)
            continue
        probabilities = counts[counts > 0] / total
        entropy = -(probabilities * np.log(probabilities)).sum()
        entropy_values.append(float(entropy / np.log(active_type_count)))
    return pd.DataFrame({"month": event_type_matrix["month"], "crisis_indicator": entropy_values})


def _build_pca_indicator(monthly: pd.DataFrame, fallback_config: dict[str, object]) -> tuple[pd.DataFrame | None, pd.DataFrame | None, float | None, list[str]]:
    candidate_features = fallback_config["candidate_features"]
    eligible_features = [
        feature
        for feature in candidate_features
        if feature in monthly.columns and monthly[feature].notna().sum() >= fallback_config["pca_min_months"] and monthly[feature].std(ddof=0) > 0
    ]

    if len(eligible_features) < fallback_config["pca_min_features"]:
        return None, None, None, eligible_features

    feature_matrix = monthly[eligible_features].fillna(0.0)
    standardized = StandardScaler().fit_transform(feature_matrix)
    pca = PCA(n_components=1)
    component = pca.fit_transform(standardized).ravel()
    loadings = pca.components_[0]

    orientation_reference = monthly["total_events"].fillna(0.0)
    correlation = pd.Series(component).corr(orientation_reference)
    if pd.notna(correlation) and correlation < 0:
        component *= -1
        loadings *= -1

    indicator = pd.DataFrame({"month": monthly["month"], "crisis_indicator": component})
    loadings_df = pd.DataFrame({"feature": eligible_features, "loading": loadings}).sort_values(
        "loading",
        key=lambda series: series.abs(),
        ascending=False,
    )
    return indicator, loadings_df.reset_index(drop=True), float(pca.explained_variance_ratio_[0]), eligible_features


def run_analysis(
    classified: pd.DataFrame,
    monthly: pd.DataFrame,
    volatility_df: pd.DataFrame,
    event_type_matrix: pd.DataFrame,
    municipality_summary: pd.DataFrame,
    config: dict[str, object],
    figures_dir: Path,
) -> dict[str, object]:
    """Run the full v2 decision tree properly aligned with v1 core sample windows."""
    target_df = volatility_df.copy()
    target_df["month"] = pd.to_datetime(target_df["date"])
    # Force alignment to explicitly defined V1 Core Calendar Window
    target_df = target_df[(target_df["month"] >= "2021-08-01") & (target_df["month"] <= "2025-12-31")]
    target_column = "colombia_cocoa_price_cop_kg_log_return"
    target_label = "Cocoa price log-return (Colombia)"
    target_df = target_df.dropna(subset=[target_column]).reset_index(drop=True)

    common_dates = set(target_df["month"]).intersection(set(monthly["month"]))
    monthly = monthly[monthly["month"].isin(common_dates)].sort_values("month").reset_index(drop=True)
    event_type_matrix = event_type_matrix[event_type_matrix["month"].isin(common_dates)].sort_values("month").reset_index(drop=True)
    target_df = target_df[target_df["month"].isin(common_dates)].sort_values("month").reset_index(drop=True)
    
    common_figures = {
        "monthly_totals": str(plot_monthly_event_totals(monthly, output_path=figures_dir / "figure_monthly_event_totals.png")),
        "hazard_mix": str(plot_hazard_domain_mix(monthly, output_path=figures_dir / "figure_hazard_domain_mix.png")),
        "municipalities": str(plot_top_municipalities(municipality_summary, output_path=figures_dir / "figure_top_municipalities.png")),
    }

    feasibility = evaluate_earthquake_feasibility(monthly, feasibility_config=config["feasibility"])
    feasibility_table = pd.DataFrame(
        [
            {
                "criterion": "Total aligned months",
                "observed_value": feasibility.total_months,
                "threshold": config["feasibility"]["min_total_months"],
                "rule": ">=",
                "passes": feasibility.total_months >= config["feasibility"]["min_total_months"],
            },
            {
                "criterion": "Non-zero aligned months",
                "observed_value": feasibility.nonzero_months,
                "threshold": config["feasibility"]["min_nonzero_months"],
                "rule": ">=",
                "passes": feasibility.nonzero_months >= config["feasibility"]["min_nonzero_months"],
            },
            {
                "criterion": "Total aligned earthquake events",
                "observed_value": feasibility.total_events,
                "threshold": config["feasibility"]["min_total_events"],
                "rule": ">=",
                "passes": feasibility.total_events >= config["feasibility"]["min_total_events"],
            },
        ]
    )

    earthquake_series = monthly[["month", "earthquake_events"]].copy()
    earthquake_series["earthquake_events"] = earthquake_series["earthquake_events"].astype(float)
    earthquake_summary = {
        "total_events": int(earthquake_series["earthquake_events"].sum()),
        "nonzero_months": int((earthquake_series["earthquake_events"] > 0).sum()),
        "max_monthly_events": int(earthquake_series["earthquake_events"].max()),
    }

    if feasibility.is_viable:
        diagnostics = _run_series_diagnostics(
            signal_df=earthquake_series,
            signal_column="earthquake_events",
            target_df=target_df,
            target_column=target_column,
            target_label=target_label,
            config=config,
            figures_dir=figures_dir,
            file_prefix="earthquake",
        )
        return {
            "branch": "earthquake",
            "branch_label": "Integrated Earthquake Time-Series Analysis",
            "branch_reason": "The monthly earthquake series satisfies all feasibility thresholds within the shared core window, triggering a full time-series integration where earthquake volatility acts as the shock predictor.",
            "feasibility": asdict(feasibility),
            "feasibility_table": feasibility_table,
            "earthquake_summary": earthquake_summary,
            "common_figures": common_figures,
            "branch_figures": diagnostics["figures"],
            "branch_tables": {
                "structural_comparison": diagnostics["structural_table"],
                "return_extension": diagnostics["model_extensions"]["return_extension"],
                "volatility_extension": diagnostics["model_extensions"]["volatility_extension"],
            },
            "branch_series": diagnostics["series_df"],
            "branch_summary": diagnostics["summary"],
            "ts_tests": diagnostics["ts_tests"],
            "change_dates": diagnostics["change_dates"],
            "shock_date": diagnostics["shock_date"],
            "selected_features": [],
            "explained_variance_ratio": None,
            "pca_loadings": pd.DataFrame(),
        }

    fallback_config = config["fallback"]
    pca_indicator, pca_loadings, explained_variance_ratio, eligible_features = _build_pca_indicator(monthly, fallback_config)
    if pca_indicator is not None and pca_loadings is not None and explained_variance_ratio is not None:
        diagnostics = _run_series_diagnostics(
            signal_df=pca_indicator,
            signal_column="crisis_indicator",
            target_df=target_df,
            target_column=target_column,
            target_label=target_label,
            config=config,
            figures_dir=figures_dir,
            file_prefix="pca_indicator",
        )
        pca_figure = plot_pca_loadings(pca_loadings, output_path=figures_dir / "figure_pca_loadings.png")
        branch_figures = dict(diagnostics["figures"])
        branch_figures["pca_loadings"] = str(pca_figure)
        return {
            "branch": "pca_index",
            "branch_label": "Composite Disaster Pressure Indicator (PCA)",
            "branch_reason": "Because earthquakes proved too sparse as an isolated continuous transmission variable across the core window, V2 strictly constructs a Composite Disaster Proxy via PCA, testing its time-series validity against cocoa markets.",
            "feasibility": asdict(feasibility),
            "feasibility_table": feasibility_table,
            "earthquake_summary": earthquake_summary,
            "common_figures": common_figures,
            "branch_figures": branch_figures,
            "branch_tables": {
                "structural_comparison": diagnostics["structural_table"],
                "pca_loadings": pca_loadings,
                "return_extension": diagnostics["model_extensions"]["return_extension"],
                "volatility_extension": diagnostics["model_extensions"]["volatility_extension"],
            },
            "branch_series": diagnostics["series_df"],
            "branch_summary": diagnostics["summary"],
            "ts_tests": diagnostics["ts_tests"],
            "change_dates": diagnostics["change_dates"],
            "shock_date": diagnostics["shock_date"],
            "selected_features": eligible_features,
            "explained_variance_ratio": explained_variance_ratio,
            "pca_loadings": pca_loadings,
        }

    months_with_events = int((event_type_matrix.drop(columns=["month"]).sum(axis=1) > 0).sum()) if not event_type_matrix.empty else 0
    distinct_event_types = int((event_type_matrix.drop(columns=["month"]).sum(axis=0) > 0).sum()) if not event_type_matrix.empty else 0
    if distinct_event_types >= fallback_config["entropy_min_event_types"] and months_with_events >= fallback_config["entropy_min_months_with_events"]:
        diagnostics = _run_series_diagnostics(
            signal_df=_build_entropy_indicator(event_type_matrix),
            signal_column="crisis_indicator",
            target_df=target_df,
            target_column=target_column,
            target_label=target_label,
            config=config,
            figures_dir=figures_dir,
            file_prefix="entropy_indicator",
        )
        return {
            "branch": "entropy_indicator",
            "branch_label": "Composite Entropy-based Hazard Dispersion",
            "branch_reason": "PCA was insufficiently supported on the aligned window, invoking a secondary composite entropy vulnerability indicator to proxy multi-hazard shocks.",
            "feasibility": asdict(feasibility),
            "feasibility_table": feasibility_table,
            "earthquake_summary": earthquake_summary,
            "common_figures": common_figures,
            "branch_figures": diagnostics["figures"],
            "branch_tables": {
                "structural_comparison": diagnostics["structural_table"],
                "return_extension": diagnostics["model_extensions"]["return_extension"],
                "volatility_extension": diagnostics["model_extensions"]["volatility_extension"],
            },
            "branch_series": diagnostics["series_df"],
            "branch_summary": diagnostics["summary"],
            "ts_tests": diagnostics["ts_tests"],
            "change_dates": diagnostics["change_dates"],
            "shock_date": diagnostics["shock_date"],
            "selected_features": [],
            "explained_variance_ratio": None,
            "pca_loadings": pd.DataFrame(),
        }

    return {
        "branch": "descriptive_only",
        "branch_label": "Descriptive analysis only",
        "branch_reason": "Failed to satisfy minimum hazard volume on the strictly aligned transmission calendar to build any viable indicator.",
        "feasibility": asdict(feasibility),
        "feasibility_table": feasibility_table,
        "earthquake_summary": earthquake_summary,
        "common_figures": common_figures,
        "branch_figures": {},
        "branch_tables": {},
        "branch_series": target_df,
        "branch_summary": _series_summary(target_df, value_column=target_column),
        "ts_tests": {"ADF_level_p": np.nan, "ADF_return_p": np.nan, "ARCH_LM_p": np.nan, "correlation_with_target": np.nan, "correlation_with_volatility": np.nan},
        "change_dates": [],
        "shock_date": None,
        "selected_features": [],
        "explained_variance_ratio": None,
        "pca_loadings": pd.DataFrame(),
    }
