"""
CHIP Estimation Pipeline

Shared pipeline steps for CHIP estimation. Used by scripts that need to
run the Cobb-Douglas distortion-factor methodology (baseline, timeseries, etc.).

This module contains the reusable computational steps. Scripts provide the
configuration (year range, country filter, deflation on/off) and call these
functions in sequence.

Pipeline Steps:
    1. map_occupations()          - Map ISCO codes to 9 occupation categories
    2. merge_labor_data()         - Join employment + wages + hours at occupation level
    3. apply_exclusions()         - Remove known data quality issues
    4. deflate_wages()            - Apply GDP deflator (optional)
    5. calculate_wage_ratios()    - Skill weights relative to Managers
    6. impute_wage_ratios()       - MICE-style imputation for missing ratios
    7. calculate_effective_labor() - Skill-weighted labor hours
    8. calculate_average_wage()   - Mean wage by country-year
    9. get_elementary_wage()      - Unskilled wage by country-year
    10. merge_with_pwt()          - Join with Penn World Tables
    11. estimate_alphas()         - Country-specific capital shares via OLS
    12. impute_alphas()           - Regression-based imputation for missing alphas
    13. calculate_mpl()           - Marginal product of labor
    14. calculate_chip()          - Distortion factor and adjusted wage
    15. aggregate_to_countries()  - Country-level averages
    16. gdp_weighted_chip()       - Global GDP-weighted CHIP value
"""

import logging

import numpy as np
import pandas as pd

from . import clean, impute

logger = logging.getLogger(__name__)


# =============================================================================
# OCCUPATION MAPPING
# =============================================================================
# The original study maps ISCO codes to 9 standardized occupation names.

ISCO_TO_OCCUPATION = {
    # ISCO-08 codes
    "OCU_ISCO08_1": "Managers",
    "OCU_ISCO08_2": "Professionals",
    "OCU_ISCO08_3": "Technicians",
    "OCU_ISCO08_4": "Clerks",
    "OCU_ISCO08_5": "Salesmen",
    "OCU_ISCO08_6": "Agforestry",
    "OCU_ISCO08_7": "Craftsmen",
    "OCU_ISCO08_8": "Operators",
    "OCU_ISCO08_9": "Elementary",
    # ISCO-88 codes
    "OCU_ISCO88_1": "Managers",
    "OCU_ISCO88_2": "Professionals",
    "OCU_ISCO88_3": "Technicians",
    "OCU_ISCO88_4": "Clerks",
    "OCU_ISCO88_5": "Salesmen",
    "OCU_ISCO88_6": "Agforestry",
    "OCU_ISCO88_7": "Craftsmen",
    "OCU_ISCO88_8": "Operators",
    "OCU_ISCO88_9": "Elementary",
}

# Codes to exclude (totals, armed forces, not classified)
EXCLUDED_CODES = [
    "OCU_SKILL_TOTAL", "OCU_ISCO08_TOTAL", "OCU_ISCO88_TOTAL",
    "OCU_ISCO08_0", "OCU_ISCO88_0",
    "OCU_ISCO08_X", "OCU_ISCO88_X", "OCU_SKILL_X",
    "OCU_SKILL_L1", "OCU_SKILL_L2", "OCU_SKILL_L3-4",
]

# Country-year exclusions (both full names and ISO codes for compatibility)
EXCLUDED_OBSERVATIONS = [
    ("Albania", 2012), ("ALB", 2012),
    ("Ghana", 2017), ("GHA", 2017),
    ("Egypt", 2009), ("EGY", 2009),
    ("Rwanda", 2014), ("RWA", 2014),
    ("Congo, Democratic Republic of the", 2005), ("COD", 2005),
    ("Côte d'Ivoire", 2019), ("CIV", 2019),
    ("Belize", 2017), ("BLZ", 2017),
]

# Countries excluded entirely (both full names and ISO codes)
EXCLUDED_COUNTRIES_LIST = [
    "Cambodia", "KHM",
    "Lao People's Democratic Republic", "LAO",
    "Timor-Leste", "TLS",
]


# =============================================================================
# STEP 1: MAP OCCUPATIONS
# =============================================================================

def map_occupations(df: pd.DataFrame, isco_col: str = "isco_code") -> pd.DataFrame:
    """
    Map ISCO codes to standardized 9-category occupation names.
    Excludes totals, armed forces, and unclassified codes.
    """
    df = df.copy()

    if isco_col not in df.columns:
        logger.warning(f"Column '{isco_col}' not found")
        return df

    df = df[~df[isco_col].isin(EXCLUDED_CODES)]
    df["occupation"] = df[isco_col].map(ISCO_TO_OCCUPATION)

    before = len(df)
    df = df.dropna(subset=["occupation"])
    after = len(df)

    if before > after:
        logger.debug(f"Mapped {after} of {before} rows to occupations")

    return df


# =============================================================================
# STEP 2: MERGE LABOR DATA
# =============================================================================

def merge_labor_data(employment: pd.DataFrame,
                     wages: pd.DataFrame,
                     hours: pd.DataFrame) -> pd.DataFrame:
    """
    Merge employment, wages, and hours at occupation level.
    Adds 'country' column from isocode if needed.
    Returns DataFrame with: country, year, occupation, employment, wage, hours, labor_hours
    """
    # Add country column from isocode if needed
    if "isocode" in employment.columns and employment["isocode"].notna().any():
        employment = employment.copy()
        wages = wages.copy()
        hours = hours.copy()
        employment["country"] = employment["isocode"]
        wages["country"] = wages["isocode"]
        hours["country"] = hours["isocode"]

    labor = employment[["country", "year", "occupation", "employment"]].copy()

    wage_cols = ["country", "year", "occupation", "wage"]
    labor = labor.merge(wages[wage_cols], on=["country", "year", "occupation"], how="left")

    if "hours" in hours.columns:
        hour_cols = ["country", "year", "occupation", "hours"]
        labor = labor.merge(hours[hour_cols], on=["country", "year", "occupation"], how="left")

    if "hours" not in labor.columns:
        labor["hours"] = 40.0
    else:
        labor["hours"] = labor["hours"].fillna(40.0)

    labor["labor_hours"] = labor["employment"] * labor["hours"]

    logger.info(f"Merged labor data: {len(labor):,} observations")
    return labor


# =============================================================================
# STEP 3: APPLY EXCLUSIONS
# =============================================================================

def apply_exclusions(labor: pd.DataFrame,
                     excluded_obs: list = None,
                     excluded_countries: list = None) -> pd.DataFrame:
    """
    Remove known data quality issues.
    Uses default exclusions from original study if not specified.
    """
    if excluded_obs is None:
        excluded_obs = EXCLUDED_OBSERVATIONS
    if excluded_countries is None:
        excluded_countries = EXCLUDED_COUNTRIES_LIST

    before = len(labor)

    for country, year in excluded_obs:
        labor = labor[~((labor["country"] == country) & (labor["year"] == year))]

    labor = labor[~labor["country"].isin(excluded_countries)]

    after = len(labor)
    if before > after:
        logger.info(f"Excluded {before - after} observations due to data quality issues")

    return labor


# =============================================================================
# STEP 4: DEFLATE WAGES (optional)
# =============================================================================

def deflate_wages(labor: pd.DataFrame, deflator: pd.DataFrame) -> pd.DataFrame:
    """
    Apply GDP deflator to convert wages to constant 2017 dollars.
    Pass deflator=None to skip deflation (nominal output).
    """
    if deflator is None:
        logger.info("Deflation DISABLED — wages in nominal dollars")
        return labor

    labor = labor.merge(deflator, on="year", how="left")
    labor["wage"] = labor["wage"] / (labor["deflator"] / 100)

    n_with_wages = labor["wage"].notna().sum()
    n_total = len(labor)
    logger.info(f"After deflation: {n_with_wages:,} of {n_total:,} observations have wages")

    return labor


# =============================================================================
# STEP 5: CALCULATE WAGE RATIOS
# =============================================================================

def calculate_wage_ratios(wages_df: pd.DataFrame,
                          reference: str = "Managers") -> pd.DataFrame:
    """
    Calculate wage ratios relative to a reference occupation.

    IMPORTANT: Calculate ratio PER COUNTRY-YEAR first, then average across years.
    Returns DataFrame with columns: country, occupation, wage_ratio
    """
    df = wages_df.copy()

    ref_wages = df[df["occupation"] == reference].copy()
    ref_wages = ref_wages[["country", "year", "wage"]].rename(columns={"wage": "ref_wage"})

    df = df.merge(ref_wages, on=["country", "year"], how="left")
    df["wage_ratio"] = df["wage"] / df["ref_wage"]

    ratios = df.groupby(["country", "occupation"])["wage_ratio"].mean().reset_index()

    logger.info(f"Calculated wage ratios for {ratios['country'].nunique()} countries")
    return ratios


# =============================================================================
# STEP 6: IMPUTE WAGE RATIOS
# =============================================================================

def impute_wage_ratios(wage_ratios: pd.DataFrame) -> pd.DataFrame:
    """
    MICE-style imputation for missing wage ratios.
    Pivots to wide format, imputes, melts back.
    """
    wage_pivot = wage_ratios.pivot(
        index="country",
        columns="occupation",
        values="wage_ratio"
    ).reset_index()

    n_missing_before = wage_pivot.isna().sum().sum()

    occ_cols = [c for c in wage_pivot.columns if c != "country"]
    wage_pivot_imputed = impute.norm_predict(wage_pivot, target_cols=occ_cols)

    n_missing_after = wage_pivot_imputed.isna().sum().sum()

    if n_missing_before > 0:
        logger.info(f"Imputed wage ratios: {n_missing_before} → {n_missing_after} missing values")

    return wage_pivot_imputed.melt(
        id_vars=["country"],
        value_vars=occ_cols,
        var_name="occupation",
        value_name="wage_ratio"
    )


# =============================================================================
# STEP 7: CALCULATE EFFECTIVE LABOR
# =============================================================================

def calculate_effective_labor(labor_df: pd.DataFrame,
                               wage_ratios: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate skill-weighted effective labor hours.
    Eff_Labor = Σ (LaborHours × WageRatio) across all occupations.
    Aggregates to country-year level.
    """
    df = labor_df.merge(wage_ratios[["country", "occupation", "wage_ratio"]],
                        on=["country", "occupation"], how="left")

    df["wage_ratio"] = df["wage_ratio"].fillna(1.0)
    df["eff_labor"] = df["labor_hours"] * df["wage_ratio"]

    eff_labor = df.groupby(["country", "year"]).agg({
        "labor_hours": "sum",
        "eff_labor": "sum",
    }).reset_index()

    logger.info(f"Calculated effective labor for {len(eff_labor)} country-years")
    return eff_labor


# =============================================================================
# STEP 8: CALCULATE AVERAGE WAGE
# =============================================================================

def calculate_average_wage(labor_df: pd.DataFrame,
                           method: str = "simple") -> pd.DataFrame:
    """
    Calculate average wage by country-year.
    method="simple": simple mean across occupations (matches reproduction)
    method="weighted": labor-weighted average
    """
    if method == "simple":
        aw_wage = labor_df.groupby(["country", "year"])["wage"].mean().reset_index()
        aw_wage = aw_wage.rename(columns={"wage": "aw_wage"})
        return aw_wage
    elif method == "weighted":
        totals = labor_df.groupby(["country", "year"])["labor_hours"].sum().reset_index()
        totals = totals.rename(columns={"labor_hours": "total_hours"})
        df = labor_df.merge(totals, on=["country", "year"])
        df["labor_share"] = df["labor_hours"] / df["total_hours"]
        df["weighted_wage"] = df["wage"] * df["labor_share"]
        aw_wage = df.groupby(["country", "year"])["weighted_wage"].sum().reset_index()
        aw_wage = aw_wage.rename(columns={"weighted_wage": "aw_wage"})
        return aw_wage
    else:
        raise ValueError(f"Unknown method: {method}")


# =============================================================================
# STEP 9: GET ELEMENTARY WAGE
# =============================================================================

def get_elementary_wage(labor_df: pd.DataFrame) -> pd.DataFrame:
    """Extract unskilled (Elementary) wage by country-year."""
    elementary = labor_df[labor_df["occupation"] == "Elementary"].copy()
    elem_wage = elementary.groupby(["country", "year"])["wage"].mean().reset_index()
    elem_wage = elem_wage.rename(columns={"wage": "elementary_wage"})
    logger.info(f"Extracted elementary wages for {len(elem_wage)} country-years")
    return elem_wage


# =============================================================================
# STEP 10: MERGE WITH PWT
# =============================================================================

def merge_with_pwt(est_data: pd.DataFrame, pwt: pd.DataFrame) -> pd.DataFrame:
    """
    Merge labor data with Penn World Tables.
    Handles isocode vs country name matching.
    Standardizes column names (rgdpna, rnna, hc).
    """
    # Determine if country column contains ISO codes
    sample_country = est_data["country"].iloc[0] if len(est_data) > 0 else ""
    is_isocode = len(str(sample_country)) == 3 and str(sample_country).isupper()

    if is_isocode and "isocode" in pwt.columns:
        est_data = est_data.rename(columns={"country": "isocode"})
        est_data = est_data.merge(pwt, on=["isocode", "year"], how="inner")
    elif "country" in pwt.columns:
        est_data = est_data.merge(pwt, on=["country", "year"], how="inner")
    else:
        est_data = est_data.merge(pwt, on=["isocode", "year"], how="inner")

    # Ensure country column exists
    if "country" not in est_data.columns and "isocode" in est_data.columns:
        est_data["country"] = est_data["isocode"]

    # Standardize PWT column names
    if "rgdpna" not in est_data.columns and "gdp" in est_data.columns:
        est_data["rgdpna"] = est_data["gdp"]
    if "rnna" not in est_data.columns:
        logger.error("rnna (real capital at national prices) not found!")
    if "hc" not in est_data.columns and "human_capital" in est_data.columns:
        est_data["hc"] = est_data["human_capital"]

    return est_data


# =============================================================================
# STEP 11: ESTIMATE ALPHAS
# =============================================================================

def estimate_alphas(est_data: pd.DataFrame) -> tuple:
    """
    Estimate country-specific capital shares (α) via OLS.

    For each country:
        ln(Y / L_eff) = α × ln(K / L_eff) + ε
    where L_eff = eff_labor × hc

    Returns (alphas_df, mean_alpha)
    """
    results = []

    for country in est_data["country"].unique():
        country_data = est_data[est_data["country"] == country]

        if len(country_data) < 3:
            continue

        try:
            L_eff = country_data["eff_labor"] * country_data["hc"]
            ln_y = np.log(country_data["rgdpna"] / L_eff)
            ln_k = np.log(country_data["rnna"] / L_eff)

            valid = np.isfinite(ln_y) & np.isfinite(ln_k)
            if valid.sum() < 3:
                continue

            ln_y = ln_y[valid].values
            ln_k = ln_k[valid].values

            X = np.column_stack([np.ones(len(ln_k)), ln_k])
            beta = np.linalg.lstsq(X, ln_y, rcond=None)[0]
            alpha = beta[1]

            if 0 < alpha < 1:
                results.append({"country": country, "alpha": alpha})

        except Exception as e:
            logger.debug(f"Alpha estimation failed for {country}: {e}")
            continue

    alphas = pd.DataFrame(results)
    mean_alpha = alphas["alpha"].mean() if len(alphas) > 0 else 0.33
    logger.info(f"Estimated alpha for {len(alphas)} countries (mean α = {mean_alpha:.3f})")

    return alphas, mean_alpha


# =============================================================================
# STEP 12: IMPUTE ALPHAS
# =============================================================================

def impute_alphas(alphas: pd.DataFrame,
                  est_data: pd.DataFrame,
                  mean_alpha: float) -> pd.DataFrame:
    """
    Impute missing alpha values using regression on ln_y and ln_k.
    Matches reproduction's MICE approach (imputation_method: "regression").
    """
    all_countries = est_data["country"].unique()
    estimated_countries = set(alphas["country"].tolist()) if len(alphas) > 0 else set()
    missing_countries = [c for c in all_countries if c not in estimated_countries]

    if len(missing_countries) == 0:
        return alphas

    logger.info(f"Imputing {len(missing_countries)} missing alpha values via regression...")

    # Calculate ln_y and ln_k per country
    country_chars = est_data.groupby("country").apply(
        lambda g: pd.Series({
            "ln_y": np.log(g["rgdpna"] / (g["eff_labor"] * g["hc"])).mean(),
            "ln_k": np.log(g["rnna"] / (g["eff_labor"] * g["hc"])).mean(),
        })
    ).reset_index()

    alphas_with_chars = alphas.merge(country_chars, on="country", how="left")
    valid_data = alphas_with_chars.dropna(subset=["alpha", "ln_y", "ln_k"])

    if len(valid_data) >= 10:
        X = valid_data[["ln_y", "ln_k"]].values
        y = valid_data["alpha"].values

        valid_mask = np.isfinite(X).all(axis=1) & np.isfinite(y)
        X = X[valid_mask]
        y = y[valid_mask]

        if len(X) < 10:
            logger.warning(f"Not enough valid data for regression ({len(X)} rows), using mean")
            fallback = pd.DataFrame({"country": missing_countries, "alpha": [mean_alpha] * len(missing_countries)})
            return pd.concat([alphas, fallback], ignore_index=True)

        X_const = np.column_stack([np.ones(len(X)), X])
        try:
            beta = np.linalg.lstsq(X_const, y, rcond=None)[0]
        except np.linalg.LinAlgError:
            logger.warning("Regression failed, using mean imputation")
            fallback = pd.DataFrame({"country": missing_countries, "alpha": [mean_alpha] * len(missing_countries)})
            return pd.concat([alphas, fallback], ignore_index=True)

        missing_chars = country_chars[country_chars["country"].isin(missing_countries)]
        missing_chars = missing_chars.dropna(subset=["ln_y", "ln_k"])
        missing_chars = missing_chars[
            np.isfinite(missing_chars["ln_y"]) & np.isfinite(missing_chars["ln_k"])
        ]

        if len(missing_chars) > 0:
            X_missing = missing_chars[["ln_y", "ln_k"]].values
            X_missing_const = np.column_stack([np.ones(len(X_missing)), X_missing])
            predicted = np.clip(X_missing_const @ beta, 0.01, 0.99)
            imputed = pd.DataFrame({"country": missing_chars["country"].values, "alpha": predicted})
            alphas = pd.concat([alphas, imputed], ignore_index=True)
            logger.info(f"Imputed {len(imputed)} alphas via regression")

        remaining = [c for c in missing_countries if c not in alphas["country"].values]
        if remaining:
            fallback = pd.DataFrame({"country": remaining, "alpha": [mean_alpha] * len(remaining)})
            alphas = pd.concat([alphas, fallback], ignore_index=True)
            logger.info(f"Imputed {len(remaining)} alphas via mean fallback")
    else:
        fallback = pd.DataFrame({"country": missing_countries, "alpha": [mean_alpha] * len(missing_countries)})
        alphas = pd.concat([alphas, fallback], ignore_index=True)
        logger.info(f"Imputed {len(missing_countries)} alphas via mean (not enough data for regression)")

    return alphas


# =============================================================================
# STEP 13: CALCULATE MPL
# =============================================================================

def calculate_mpl(data: pd.DataFrame, default_alpha: float) -> pd.DataFrame:
    """
    Calculate Marginal Product of Labor.
    MPL = (1 - α) × (K / L_eff × hc)^α
    Note: hc is INSIDE the power (matches original R code).
    Expects 'alpha' column already in data.
    """
    df = data.copy()
    df["alpha"] = df["alpha"].fillna(default_alpha)
    df["k_per_l_hc"] = (df["rnna"] / df["eff_labor"]) * df["hc"]
    df["mpl"] = (1 - df["alpha"]) * np.power(df["k_per_l_hc"], df["alpha"])
    return df


# =============================================================================
# STEP 14: CALCULATE CHIP (distortion factor + adjusted wage)
# =============================================================================

def calculate_chip(est_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate distortion factor and adjusted elementary wage (CHIP).
    θ = MPL / AW_Wage
    CHIP = Elementary_Wage × θ
    """
    df = est_data.copy()
    df["theta"] = df["mpl"] / df["aw_wage"]
    df["chip_value"] = df["elementary_wage"] * df["theta"]
    return df


# =============================================================================
# STEP 15: AGGREGATE TO COUNTRIES
# =============================================================================

def aggregate_to_countries(est_data: pd.DataFrame) -> pd.DataFrame:
    """Average across years for each country."""
    country_data = est_data.groupby("country").agg({
        "chip_value": "mean",
        "elementary_wage": "mean",
        "theta": "mean",
        "alpha": "mean",
        "mpl": "mean",
        "rgdpna": "mean",
        "year": ["min", "max", "count"],
    }).reset_index()

    country_data.columns = [
        "country", "chip_value", "elementary_wage", "theta", "alpha", "mpl",
        "gdp", "year_min", "year_max", "n_years"
    ]

    logger.info(f"Aggregated to {len(country_data)} countries")
    return country_data


# =============================================================================
# STEP 16: GDP-WEIGHTED CHIP
# =============================================================================

def gdp_weighted_chip(country_data: pd.DataFrame) -> float:
    """Calculate GDP-weighted global CHIP value."""
    total_gdp = country_data["gdp"].sum()
    country_data = country_data.copy()
    country_data["gdp_weight"] = country_data["gdp"] / total_gdp
    chip_value = (country_data["chip_value"] * country_data["gdp_weight"]).sum()
    logger.info(f"Global CHIP (GDP-weighted): ${chip_value:.2f}/hour")
    return chip_value


# =============================================================================
# HIGH-LEVEL PIPELINE RUNNER
# =============================================================================

def prepare_labor_data(data: dict,
                       year_start: int,
                       year_end: int,
                       deflator_df: pd.DataFrame = None,
                       include_countries: list = None,
                       enable_imputation: bool = True,
                       wage_averaging_method: str = "simple") -> dict:
    """
    Run steps 1-10: from raw data to estimation-ready dataset.

    Args:
        data: dict from fetcher.get_all()
        year_start, year_end: year range filter
        deflator_df: normalized deflator DataFrame, or None to skip deflation
        include_countries: list of country codes/names to include, or None for all
        enable_imputation: whether to impute missing wage ratios
        wage_averaging_method: "simple" or "weighted"

    Returns:
        dict with keys:
            "est_data" - merged dataset ready for alpha estimation
            "labor_with_wages" - labor rows that have wage data
            "eff_labor" - effective labor by country-year
            "aw_wage" - average wage by country-year
            "elem_wage" - elementary wage by country-year
    """
    from . import normalize

    # Normalize
    employment = normalize.normalize_ilostat(data["employment"], "employment")
    wages = normalize.normalize_ilostat(data["wages"], "wage")
    hours = normalize.normalize_ilostat(data["hours"], "hours")
    pwt = normalize.normalize_pwt(data["pwt"])

    # Filter years
    employment = clean.filter_years(employment, year_start, year_end)
    wages = clean.filter_years(wages, year_start, year_end)
    hours = clean.filter_years(hours, year_start, year_end)
    pwt = clean.filter_years(pwt, year_start, year_end)

    # Filter wages to USD
    if "currency_code" in wages.columns:
        wages = wages[wages["currency_code"].str.contains("USD", case=False, na=False)]
        logger.info(f"Filtered to USD wages: {len(wages):,} rows")

    # Filter to sex totals
    for name in ["employment", "wages", "hours"]:
        df = {"employment": employment, "wages": wages, "hours": hours}[name]
        if "sex" in df.columns:
            before = len(df)
            filtered = df[df["sex"].str.contains("SEX_T|total", case=False, na=False)]
            logger.info(f"Filtered {name} to totals: {len(filtered):,} rows (was {before:,})")
            if name == "employment":
                employment = filtered
            elif name == "wages":
                wages = filtered
            else:
                hours = filtered

    # Map occupations
    employment = map_occupations(employment)
    wages = map_occupations(wages)
    hours = map_occupations(hours)

    # Merge labor data
    labor = merge_labor_data(employment, wages, hours)

    # Country filtering
    if include_countries is not None and len(include_countries) > 0:
        labor = clean.include_countries(labor, include_countries, country_col="country")
        if len(labor) == 0:
            raise ValueError("No matching countries found!")

    # Apply exclusions
    labor = apply_exclusions(labor)

    # Deflation (optional)
    labor = deflate_wages(labor, deflator_df)

    # Wage ratios (from rows WITH wages only)
    labor_with_wages = labor.dropna(subset=["wage"])
    wage_ratios = calculate_wage_ratios(labor_with_wages, reference="Managers")

    if enable_imputation:
        wage_ratios = impute_wage_ratios(wage_ratios)

    # Effective labor (from ALL employment)
    eff_labor = calculate_effective_labor(labor, wage_ratios)

    # Average and elementary wages (from rows WITH wages)
    aw_wage = calculate_average_wage(labor_with_wages, method=wage_averaging_method)
    elem_wage = get_elementary_wage(labor_with_wages)

    # Merge with PWT
    est_data = eff_labor.copy()
    est_data = est_data.merge(aw_wage, on=["country", "year"], how="left")
    est_data = est_data.merge(elem_wage, on=["country", "year"], how="left")

    # Drop country column from PWT to avoid collision
    pwt_no_country = pwt.drop(columns=["country"]) if "country" in pwt.columns else pwt
    est_data = merge_with_pwt(est_data, pwt_no_country)

    return {
        "est_data": est_data,
        "labor_with_wages": labor_with_wages,
        "eff_labor": eff_labor,
        "aw_wage": aw_wage,
        "elem_wage": elem_wage,
    }


def estimate_chip(est_data: pd.DataFrame,
                  enable_imputation: bool = True) -> tuple:
    """
    Run steps 11-16: from estimation data to global CHIP value.

    Args:
        est_data: output of prepare_labor_data()["est_data"]
        enable_imputation: whether to impute missing alphas

    Returns:
        (chip_value, country_data, est_data_with_chip)
    """
    # Alpha estimation on full PWT data (not just rows with wages)
    alpha_required = ["eff_labor", "rgdpna", "rnna", "hc"]
    alpha_available = [c for c in alpha_required if c in est_data.columns]
    est_data_for_alpha = est_data.dropna(subset=alpha_available)

    logger.info(f"Data for alpha estimation: {len(est_data_for_alpha)} observations, "
                f"{est_data_for_alpha['country'].nunique()} countries")

    alphas, mean_alpha = estimate_alphas(est_data_for_alpha)

    if enable_imputation:
        alphas = impute_alphas(alphas, est_data_for_alpha, mean_alpha)

    # Merge alphas and filter to rows with wage data
    est_data = est_data.merge(alphas[["country", "alpha"]], on="country", how="left")

    wage_required = ["eff_labor", "aw_wage", "elementary_wage", "rgdpna", "rnna", "hc", "alpha"]
    wage_available = [c for c in wage_required if c in est_data.columns]
    est_data = est_data.dropna(subset=wage_available)

    logger.info(f"After filtering for wage data: {len(est_data)} observations, "
                f"{est_data['country'].nunique()} countries")

    # MPL, distortion factor, CHIP
    est_data = calculate_mpl(est_data, mean_alpha)
    est_data = calculate_chip(est_data)

    # Aggregate to countries and compute global CHIP
    country_data = aggregate_to_countries(est_data)
    chip_value = gdp_weighted_chip(country_data)

    return chip_value, country_data, est_data
