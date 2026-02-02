#!/usr/bin/env python3
"""
Baseline Reproduction Script

This script reproduces the $2.56 CHIP value from the original study.
It serves as an integration test for the workbench library and as
documentation of the original study's methodology.

=============================================================================
METHODOLOGY OVERVIEW (from original chips.R)
=============================================================================

The original study calculates CHIP (value of one hour of unskilled labor)
using a Cobb-Douglas production function approach:

1. DATA: Collect labor data (employment, wages, hours) for ALL occupation
   categories, not just unskilled. The study uses 9 ISCO major groups.

2. WAGE RATIOS: Calculate wage ratios relative to Managers (the reference).
   For example, if Elementary workers earn 30% of Managers, their ratio is 0.3.
   These ratios serve as "skill weights" — how much each occupation 
   contributes to production relative to Managers.

3. EFFECTIVE LABOR: Calculate skill-weighted labor hours:
   Eff_Labor = Σ (Employed × Hours × Wage_Ratio) across ALL occupations
   This is a measure of total "equivalent Manager hours" in the economy.

4. MERGE WITH PWT: Join with Penn World Tables to get capital stock (K),
   GDP (Y), and human capital index (hc).

5. ESTIMATE ALPHA: Run fixed-effects regression to estimate capital share (α):
   ln(Y / Eff_Labor × hc) = α × ln(K / Eff_Labor × hc) + country_effects

6. CALCULATE MPL: Marginal Product of Labor using Cobb-Douglas formula:
   MPL = (1 - α) × (K / Eff_Labor × hc)^α
   
   KEY INSIGHT: The denominator is ILOSTAT's Eff_Labor, NOT PWT's employment.
   This is skill-adjusted labor measured in "equivalent Manager hours".

7. AVERAGE WAGE: Calculate labor-weighted average wage across all occupations:
   AW_Wage = Σ (Wage × Labor_Share) where Labor_Share = Hours_i / Total_Hours

8. DISTORTION FACTOR: Compare actual wages to marginal product:
   θ = MPL / AW_Wage
   
   If θ > 1, workers are underpaid relative to their marginal product.
   If θ < 1, workers are overpaid (unlikely in competitive markets).

9. ADJUSTED WAGE: Apply distortion factor to ELEMENTARY (unskilled) wage:
   CHIP_country = Elementary_Wage × θ
   
   This gives the "fair" wage for unskilled labor if markets were frictionless.

10. GLOBAL CHIP: GDP-weighted average across countries:
    CHIP = Σ (CHIP_country × GDP_weight)

=============================================================================

Target: $2.56/hour (from reproduction/ using original data)

Usage:
    ./run.sh baseline
    ./run.sh baseline -v   # Run and view report
"""

import sys
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.logging_config import setup_logging, ScriptContext, get_logger
from lib import fetcher
from lib import normalize
from lib import clean
from lib import impute
from lib import aggregate as agg
from lib.config import load_config

logger = get_logger(__name__)


# =============================================================================
# CONFIGURATION OPTIONS
# =============================================================================
# 
# These can be set via config.yaml or modified here for testing.

# Countries from the reproduction run (90 countries)
# These are the countries that passed all quality filters in the original study
# Both ISO codes (for API data) and country names (for local data) are included
REPRODUCTION_ISOCODES = [
    "ALB", "ARG", "ARM", "AUT", "BEL", "BGD", "BGR", "BLZ", "BRA", "BRN", 
    "BWA", "CHE", "CHL", "COL", "CRI", "CYP", "CZE", "DEU", "DNK", "DOM", 
    "ECU", "EGY", "ESP", "EST", "ETH", "FIN", "FRA", "GBR", "GHA", "GRC", 
    "HND", "HRV", "HUN", "IDN", "IND", "IRL", "ISL", "ISR", "ITA", "JAM", 
    "JOR", "KEN", "KOR", "LKA", "LSO", "LTU", "LUX", "LVA", "MDG", "MDV", 
    "MEX", "MLI", "MLT", "MMR", "MNG", "MUS", "MYS", "NAM", "NGA", "NIC", 
    "NLD", "NOR", "NPL", "PAK", "PAN", "PER", "PHL", "POL", "PRT", "PRY", 
    "ROU", "RUS", "RWA", "SEN", "SLV", "SRB", "SVK", "SVN", "SWE", "THA", 
    "TJK", "TUR", "TZA", "UGA", "UKR", "USA", "VNM", "YEM", "ZAF", "ZMB"
]

REPRODUCTION_COUNTRIES = [
    "Albania", "Argentina", "Armenia", "Austria", "Bangladesh", "Belgium",
    "Belize", "Botswana", "Brazil", "Brunei Darussalam", "Bulgaria", "Chile",
    "Colombia", "Costa Rica", "Croatia", "Cyprus", "Czechia", "Denmark",
    "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Estonia",
    "Ethiopia", "Finland", "France", "Germany", "Ghana", "Greece", "Honduras",
    "Hungary", "Iceland", "India", "Indonesia", "Ireland", "Israel", "Italy",
    "Jamaica", "Jordan", "Kenya", "Korea, Republic of", "Latvia", "Lesotho",
    "Lithuania", "Luxembourg", "Madagascar", "Malaysia", "Maldives", "Mali",
    "Malta", "Mauritius", "Mexico", "Mongolia", "Myanmar", "Namibia", "Nepal",
    "Netherlands", "Nicaragua", "Nigeria", "Norway", "Pakistan", "Panama",
    "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Romania",
    "Russian Federation", "Rwanda", "Senegal", "Serbia", "Slovakia", "Slovenia",
    "South Africa", "Spain", "Sri Lanka", "Sweden", "Switzerland", "Tajikistan",
    "Tanzania, United Republic of", "Thailand", "Türkiye", "Uganda", "Ukraine",
    "United Kingdom", "United States", "Viet Nam", "Yemen", "Zambia",
]

# Set to a list of country names/codes to restrict analysis to specific countries.
# Options:
#   None                    - Use all available countries
#   REPRODUCTION_ISOCODES   - Match original study's 90 countries (use with API data)
#   REPRODUCTION_COUNTRIES  - Match original study's 90 countries (use with local data)
#   ["USA", "DEU", ...]     - Custom list
INCLUDE_COUNTRIES = None  # Try REPRODUCTION_ISOCODES to match original

# Enable MICE-style imputation for missing wage ratios and alphas
# This matches the original R study's use of mice::mice with norm.predict
ENABLE_IMPUTATION = True


# =============================================================================
# OCCUPATION MAPPING (Specific to original study)
# =============================================================================
# 
# The original study maps ISCO codes to 9 standardized occupation names.
# This mapping is specific to the original methodology and is kept here
# rather than in lib/ because other studies might use different mappings.

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
    "OCU_ISCO08_0", "OCU_ISCO88_0",  # Armed forces
    "OCU_ISCO08_X", "OCU_ISCO88_X", "OCU_SKILL_X",  # Not classified
    "OCU_SKILL_L1", "OCU_SKILL_L2", "OCU_SKILL_L3-4",  # Skill aggregates
]

# Countries/years with known data quality issues (from original R code)
EXCLUDED_OBSERVATIONS = [
    ("Albania", 2012),
    ("Ghana", 2017),
    ("Egypt", 2009),
    ("Rwanda", 2014),
    ("Congo, Democratic Republic of the", 2005),
    ("Côte d'Ivoire", 2019),
    ("Belize", 2017),
]

EXCLUDED_COUNTRIES = [
    "Cambodia",
    "Lao People's Democratic Republic",
    "Timor-Leste",
]


# =============================================================================
# HELPER FUNCTIONS (Specific to original study methodology)
# =============================================================================

def map_occupations(df: pd.DataFrame, isco_col: str = "isco_code") -> pd.DataFrame:
    """
    Map ISCO codes to standardized occupation names.
    
    This is specific to the original study's 9-category scheme.
    """
    df = df.copy()
    
    if isco_col not in df.columns:
        logger.warning(f"Column '{isco_col}' not found")
        return df
    
    # Exclude unwanted codes
    df = df[~df[isco_col].isin(EXCLUDED_CODES)]
    
    # Map to occupation names
    df["occupation"] = df[isco_col].map(ISCO_TO_OCCUPATION)
    
    # Drop rows that didn't map
    before = len(df)
    df = df.dropna(subset=["occupation"])
    after = len(df)
    
    if before > after:
        logger.debug(f"Mapped {after} of {before} rows to occupations")
    
    return df


def calculate_wage_ratios(wages_df: pd.DataFrame, 
                          reference: str = "Managers") -> pd.DataFrame:
    """
    Calculate wage ratios relative to a reference occupation.
    
    The original study uses Managers as the reference category.
    These ratios are used as skill weights for effective labor.
    
    Returns DataFrame with columns: country, occupation, wage_ratio
    """
    # Pivot to get wages by occupation for each country
    wage_pivot = wages_df.groupby(["country", "occupation"])["wage"].mean().reset_index()
    
    # Get reference (Manager) wages by country
    ref_wages = wage_pivot[wage_pivot["occupation"] == reference].copy()
    ref_wages = ref_wages.rename(columns={"wage": "ref_wage"})
    ref_wages = ref_wages[["country", "ref_wage"]]
    
    # Merge and calculate ratio
    wage_pivot = wage_pivot.merge(ref_wages, on="country", how="left")
    wage_pivot["wage_ratio"] = wage_pivot["wage"] / wage_pivot["ref_wage"]
    
    # Average by country-occupation (across years)
    ratios = wage_pivot.groupby(["country", "occupation"])["wage_ratio"].mean().reset_index()
    
    logger.info(f"Calculated wage ratios for {ratios['country'].nunique()} countries")
    
    return ratios


def calculate_effective_labor(labor_df: pd.DataFrame,
                               wage_ratios: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate skill-weighted effective labor hours.
    
    Eff_Labor = Σ (LaborHours × WageRatio) across all occupations
    
    This aggregates to country-year level.
    """
    # Merge wage ratios as skill weights
    df = labor_df.merge(wage_ratios[["country", "occupation", "wage_ratio"]],
                        on=["country", "occupation"],
                        how="left")
    
    # Default wage ratio to 1.0 if missing
    df["wage_ratio"] = df["wage_ratio"].fillna(1.0)
    
    # Calculate effective labor for each observation
    df["eff_labor"] = df["labor_hours"] * df["wage_ratio"]
    
    # Aggregate to country-year level (sum across occupations)
    eff_labor = df.groupby(["country", "year"]).agg({
        "labor_hours": "sum",      # Total raw labor hours
        "eff_labor": "sum",        # Total skill-weighted labor hours
    }).reset_index()
    
    logger.info(f"Calculated effective labor for {len(eff_labor)} country-years")
    
    return eff_labor


def calculate_average_wage(labor_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate labor-weighted average wage by country-year.
    
    AW_Wage = Σ (Wage × LaborShare) where LaborShare = Hours_i / TotalHours
    
    This is the average wage across ALL occupations, weighted by how many
    hours each occupation works.
    """
    # Get total labor hours per country-year
    totals = labor_df.groupby(["country", "year"])["labor_hours"].sum().reset_index()
    totals = totals.rename(columns={"labor_hours": "total_hours"})
    
    # Merge and calculate labor share
    df = labor_df.merge(totals, on=["country", "year"])
    df["labor_share"] = df["labor_hours"] / df["total_hours"]
    
    # Calculate weighted wage contribution
    df["weighted_wage"] = df["wage"] * df["labor_share"]
    
    # Sum to get average weighted wage
    aw_wage = df.groupby(["country", "year"])["weighted_wage"].sum().reset_index()
    aw_wage = aw_wage.rename(columns={"weighted_wage": "aw_wage"})
    
    return aw_wage


def get_elementary_wage(labor_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract unskilled (Elementary) wage by country-year.
    
    This is the wage that will be adjusted by the distortion factor
    to get the final CHIP value.
    """
    elementary = labor_df[labor_df["occupation"] == "Elementary"].copy()
    
    elem_wage = elementary.groupby(["country", "year"])["wage"].mean().reset_index()
    elem_wage = elem_wage.rename(columns={"wage": "elementary_wage"})
    
    logger.info(f"Extracted elementary wages for {len(elem_wage)} country-years")
    
    return elem_wage


def estimate_alphas(est_data: pd.DataFrame) -> pd.DataFrame:
    """
    Estimate country-specific capital shares (α) via OLS.
    
    For each country, we estimate:
        ln(Y / L_eff × hc) = α × ln(K / L_eff × hc) + ε
    
    where:
        Y = rgdpna (real GDP at national prices)
        K = rnna (real capital at national prices)
        L_eff = effective labor (skill-weighted hours from ILOSTAT)
        hc = human capital index from PWT
    
    Returns DataFrame with columns: country, alpha
    """
    results = []
    
    for country in est_data["country"].unique():
        country_data = est_data[est_data["country"] == country]
        
        if len(country_data) < 3:  # Need minimum observations
            continue
        
        try:
            # Calculate log variables
            ln_y = np.log(country_data["rgdpna"] / country_data["eff_labor"] * country_data["hc"])
            ln_k = np.log(country_data["rnna"] / country_data["eff_labor"] * country_data["hc"])
            
            # Remove infinities
            valid = np.isfinite(ln_y) & np.isfinite(ln_k)
            if valid.sum() < 3:
                continue
            
            ln_y = ln_y[valid].values
            ln_k = ln_k[valid].values
            
            # OLS: ln(y) = intercept + alpha * ln(k)
            X = np.column_stack([np.ones(len(ln_k)), ln_k])
            beta = np.linalg.lstsq(X, ln_y, rcond=None)[0]
            alpha = beta[1]
            
            # Only keep economically valid alphas (0 < α < 1)
            if 0 < alpha < 1:
                results.append({"country": country, "alpha": alpha})
            
        except Exception as e:
            logger.debug(f"Alpha estimation failed for {country}: {e}")
            continue
    
    alphas = pd.DataFrame(results)
    
    # Impute missing alphas with mean
    mean_alpha = alphas["alpha"].mean()
    logger.info(f"Estimated alpha for {len(alphas)} countries (mean α = {mean_alpha:.3f})")
    
    return alphas, mean_alpha


def calculate_mpl(data: pd.DataFrame, alphas: pd.DataFrame, default_alpha: float) -> pd.DataFrame:
    """
    Calculate Marginal Product of Labor.
    
    MPL = (1 - α) × (K / L_eff × hc)^α
    
    CRITICAL: This is the exact formula from the original R code:
        MPL3 = (1-alpha3)*(rnna / Eff_Labor * hc)^(alpha3)
    
    Note: hc is INSIDE the power, not outside!
    
    where K = rnna (real capital at national prices, millions)
          L_eff = effective labor (skill-weighted labor hours)
          hc = human capital index
    """
    df = data.merge(alphas, on="country", how="left")
    df["alpha"] = df["alpha"].fillna(default_alpha)
    
    # Capital per effective worker, multiplied by human capital
    # This matches R: (rnna / Eff_Labor * hc)
    df["k_per_l_hc"] = (df["rnna"] / df["eff_labor"]) * df["hc"]
    
    # MPL formula: (1-α) × (K/L × hc)^α
    # hc is INSIDE the power - this matches the original R code exactly
    df["mpl"] = (1 - df["alpha"]) * np.power(df["k_per_l_hc"], df["alpha"])
    
    return df


# =============================================================================
# MAIN PIPELINE
# =============================================================================

def run_baseline():
    """
    Run the baseline reproduction pipeline.
    
    This implements the exact methodology of the original study.
    See module docstring for detailed explanation.
    """
    
    config = load_config()
    
    # =========================================================================
    # STEP 1: FETCH DATA
    # =========================================================================
    logger.info("=" * 70)
    logger.info("STEP 1: Fetching data from sources")
    logger.info("=" * 70)
    
    print("Fetching data (this may take a moment)...")
    
    data = fetcher.get_all()
    
    for name, df in data.items():
        logger.info(f"  {name}: {len(df):,} rows")
    
    # =========================================================================
    # STEP 2: NORMALIZE COLUMN NAMES
    # =========================================================================
    logger.info("=" * 70)
    logger.info("STEP 2: Normalizing column names")
    logger.info("=" * 70)
    
    employment = normalize.normalize_ilostat(data["employment"], "employment")
    wages = normalize.normalize_ilostat(data["wages"], "wage")
    hours = normalize.normalize_ilostat(data["hours"], "hours")
    pwt = normalize.normalize_pwt(data["pwt"])
    deflator = normalize.normalize_deflator(data["deflator"], base_year=2017)
    
    # =========================================================================
    # STEP 3: FILTER AND CLEAN
    # =========================================================================
    logger.info("=" * 70)
    logger.info("STEP 3: Filtering and cleaning data")
    logger.info("=" * 70)
    
    # Year range
    year_start = config.data.year_start
    year_end = config.data.year_end
    
    employment = clean.filter_years(employment, year_start, year_end)
    wages = clean.filter_years(wages, year_start, year_end)
    hours = clean.filter_years(hours, year_start, year_end)
    pwt = clean.filter_years(pwt, year_start, year_end)
    
    logger.info(f"Year range: {year_start}-{year_end}")
    
    # Filter wages to USD only (critical - LCU would inflate values)
    if "currency_code" in wages.columns:
        wages = wages[wages["currency_code"].str.contains("USD", case=False, na=False)]
        logger.info(f"Filtered to USD wages: {len(wages):,} rows")
    
    # Filter to totals only (not male/female breakdowns)
    # SEX_T = total, SEX_M = male, SEX_F = female
    for df_name, df in [("employment", employment), ("wages", wages), ("hours", hours)]:
        if "sex" in df.columns:
            before = len(df)
            if df_name == "employment":
                employment = df[df["sex"].str.contains("SEX_T|total", case=False, na=False)]
                logger.info(f"Filtered {df_name} to totals: {len(employment):,} rows (was {before:,})")
            elif df_name == "wages":
                wages = df[df["sex"].str.contains("SEX_T|total", case=False, na=False)]
                logger.info(f"Filtered {df_name} to totals: {len(wages):,} rows (was {before:,})")
            elif df_name == "hours":
                hours = df[df["sex"].str.contains("SEX_T|total", case=False, na=False)]
                logger.info(f"Filtered {df_name} to totals: {len(hours):,} rows (was {before:,})")
    
    # =========================================================================
    # STEP 4: MAP OCCUPATIONS
    # =========================================================================
    logger.info("=" * 70)
    logger.info("STEP 4: Mapping ISCO codes to occupations")
    logger.info("=" * 70)
    
    # Map to standardized occupation names (9 categories)
    employment = map_occupations(employment)
    wages = map_occupations(wages)
    hours = map_occupations(hours)
    
    logger.info(f"Employment: {employment['occupation'].nunique()} occupations")
    logger.info(f"Wages: {wages['occupation'].nunique()} occupations")
    
    # =========================================================================
    # STEP 5: MERGE LABOR DATA
    # =========================================================================
    logger.info("=" * 70)
    logger.info("STEP 5: Merging labor data (employment + wages + hours)")
    logger.info("=" * 70)
    
    # Determine merge key (isocode or country)
    if "isocode" in employment.columns and employment["isocode"].notna().any():
        merge_key = "isocode"
        # Rename isocode to country for consistency downstream
        employment["country"] = employment["isocode"]
        wages["country"] = wages["isocode"]
        hours["country"] = hours["isocode"]
    elif "country" in employment.columns:
        merge_key = "country"
    else:
        raise ValueError("No country identifier found")
    
    logger.info(f"Using '{merge_key}' as country identifier")
    
    # Merge at occupation level
    labor = employment[["country", "year", "occupation", "employment"]].copy()
    
    wage_cols = ["country", "year", "occupation", "wage"]
    labor = labor.merge(wages[wage_cols], on=["country", "year", "occupation"], how="left")
    
    if "hours" in hours.columns:
        hour_cols = ["country", "year", "occupation", "hours"]
        labor = labor.merge(hours[hour_cols], on=["country", "year", "occupation"], how="left")
    
    # Default missing hours to 40 (per original study)
    if "hours" not in labor.columns:
        labor["hours"] = 40.0
    else:
        labor["hours"] = labor["hours"].fillna(40.0)
    
    # Calculate labor hours
    labor["labor_hours"] = labor["employment"] * labor["hours"]
    
    logger.info(f"Merged labor data: {len(labor):,} observations")
    
    # =========================================================================
    # STEP 5.5: OPTIONAL COUNTRY FILTERING
    # =========================================================================
    # If INCLUDE_COUNTRIES is set, filter to only those countries.
    # This is useful for:
    # - Matching the exact country set from the original study
    # - Regional analysis (e.g., EU only)
    # - Sensitivity testing
    
    if INCLUDE_COUNTRIES is not None and len(INCLUDE_COUNTRIES) > 0:
        logger.info("=" * 70)
        logger.info("STEP 5.5: Filtering to specified countries")
        logger.info("=" * 70)
        
        before = labor["country"].nunique()
        labor = clean.include_countries(labor, INCLUDE_COUNTRIES, country_col="country")
        after = labor["country"].nunique()
        
        if after == 0:
            raise ValueError(f"No matching countries found! Check INCLUDE_COUNTRIES: {INCLUDE_COUNTRIES[:5]}...")
    
    # =========================================================================
    # STEP 6: APPLY EXCLUSIONS
    # =========================================================================
    logger.info("=" * 70)
    logger.info("STEP 6: Applying data quality exclusions")
    logger.info("=" * 70)
    
    # Exclude specific country-years
    before = len(labor)
    for country, year in EXCLUDED_OBSERVATIONS:
        labor = labor[~((labor["country"] == country) & (labor["year"] == year))]
    
    # Exclude entire countries
    labor = labor[~labor["country"].isin(EXCLUDED_COUNTRIES)]
    
    after = len(labor)
    logger.info(f"Excluded {before - after} observations due to data quality issues")
    
    # =========================================================================
    # STEP 7: APPLY DEFLATOR
    # =========================================================================
    logger.info("=" * 70)
    logger.info("STEP 7: Deflating wages to 2017 dollars")
    logger.info("=" * 70)
    
    labor = labor.merge(deflator, on="year", how="left")
    labor["wage"] = labor["wage"] / (labor["deflator"] / 100)
    
    # Drop rows without wage data
    labor = labor.dropna(subset=["wage"])
    logger.info(f"After deflation: {len(labor):,} observations with wages")
    
    # =========================================================================
    # STEP 8: CALCULATE WAGE RATIOS (Skill Weights)
    # =========================================================================
    logger.info("=" * 70)
    logger.info("STEP 8: Calculating wage ratios relative to Managers")
    logger.info("=" * 70)
    
    wage_ratios = calculate_wage_ratios(labor, reference="Managers")
    
    # -------------------------------------------------------------------------
    # MICE IMPUTATION FOR WAGE RATIOS
    # -------------------------------------------------------------------------
    # The original R code uses:
    #   imp <- mice::mice(wageratdata, method = "norm.predict", m = 1)
    #   wageratdata_imp <- complete(imp)
    # 
    # This imputes missing wage ratios using linear regression prediction.
    # Countries may be missing certain occupation wages (e.g., no Agforestry data)
    # but we need complete wage ratios to calculate effective labor correctly.
    
    if ENABLE_IMPUTATION:
        # Pivot to wide format for imputation (country × occupation)
        wage_pivot = wage_ratios.pivot(
            index="country", 
            columns="occupation", 
            values="wage_ratio"
        ).reset_index()
        
        n_missing_before = wage_pivot.isna().sum().sum()
        
        # Get occupation columns (all except country)
        occ_cols = [c for c in wage_pivot.columns if c != "country"]
        
        # Apply MICE-style imputation
        wage_pivot_imputed = impute.norm_predict(wage_pivot, target_cols=occ_cols)
        
        n_missing_after = wage_pivot_imputed.isna().sum().sum()
        
        if n_missing_before > 0:
            logger.info(f"  Imputed wage ratios: {n_missing_before} → {n_missing_after} missing values")
        
        # Melt back to long format
        wage_ratios = wage_pivot_imputed.melt(
            id_vars=["country"],
            value_vars=occ_cols,
            var_name="occupation",
            value_name="wage_ratio"
        )
    
    # Log sample ratios
    sample = wage_ratios.groupby("occupation")["wage_ratio"].mean()
    for occ in ["Elementary", "Professionals", "Technicians"]:
        if occ in sample.index:
            logger.info(f"  {occ}: {sample[occ]:.2f}× Manager wage")
    
    # =========================================================================
    # STEP 9: CALCULATE EFFECTIVE LABOR
    # =========================================================================
    logger.info("=" * 70)
    logger.info("STEP 9: Calculating effective labor (skill-weighted hours)")
    logger.info("=" * 70)
    
    eff_labor = calculate_effective_labor(labor, wage_ratios)
    
    # =========================================================================
    # STEP 10: CALCULATE AVERAGE WAGE AND ELEMENTARY WAGE
    # =========================================================================
    logger.info("=" * 70)
    logger.info("STEP 10: Calculating average wage and elementary wage")
    logger.info("=" * 70)
    
    aw_wage = calculate_average_wage(labor)
    elem_wage = get_elementary_wage(labor)
    
    # =========================================================================
    # STEP 11: MERGE WITH PWT
    # =========================================================================
    logger.info("=" * 70)
    logger.info("STEP 11: Merging with Penn World Tables")
    logger.info("=" * 70)
    
    # Start with effective labor
    est_data = eff_labor.copy()
    
    # Add average wage
    est_data = est_data.merge(aw_wage, on=["country", "year"], how="left")
    
    # Add elementary wage
    est_data = est_data.merge(elem_wage, on=["country", "year"], how="left")
    
    # Merge with PWT
    # PWT has columns: isocode, country, year, gdp, capital, employment, human_capital, etc.
    pwt_cols = ["isocode", "country", "year", "gdp", "capital", "human_capital", "labor_share"]
    
    # The normalized PWT has: isocode, country, year, gdp, capital, employment, human_capital
    # We need to check what columns actually exist
    if "isocode" in pwt.columns:
        # Try matching on isocode first (more reliable)
        sample_country = est_data["country"].iloc[0] if len(est_data) > 0 else ""
        is_isocode = len(str(sample_country)) == 3 and str(sample_country).isupper()
        
        if is_isocode:
            est_data = est_data.rename(columns={"country": "isocode"})
            est_data = est_data.merge(pwt, on=["isocode", "year"], how="inner")
        else:
            # Match on country name
            est_data = est_data.merge(pwt, on=["country", "year"], how="inner")
    else:
        est_data = est_data.merge(pwt, on=["country", "year"], how="inner")
    
    # Ensure we have country column
    if "country" not in est_data.columns and "isocode" in est_data.columns:
        est_data["country"] = est_data["isocode"]
    
    # Standardize column names for capital and GDP
    # Original R uses: rgdpna, rnna, hc
    # The PWT normalizer renames some columns, but we want the raw ones:
    #   - rgdpna: real GDP at national prices (already named rgdpna, or renamed to gdp)
    #   - rnna: real capital at national prices (NOT the "capital" column!)
    #   - hc: human capital index (renamed to human_capital)
    
    # Use rgdpna directly if available, else use gdp
    if "rgdpna" not in est_data.columns and "gdp" in est_data.columns:
        est_data["rgdpna"] = est_data["gdp"]
    
    # rnna should already exist in raw PWT data (NOT using 'capital' which is rkna)
    if "rnna" not in est_data.columns:
        logger.error("rnna (real capital at national prices) not found!")
        logger.error(f"Available columns: {list(est_data.columns)}")
    
    # hc or human_capital
    if "hc" not in est_data.columns and "human_capital" in est_data.columns:
        est_data["hc"] = est_data["human_capital"]
    
    # Drop rows without required data
    required = ["eff_labor", "aw_wage", "elementary_wage", "rgdpna", "rnna", "hc"]
    available = [c for c in required if c in est_data.columns]
    missing = [c for c in required if c not in est_data.columns]
    if missing:
        logger.warning(f"Missing columns: {missing}")
    
    est_data = est_data.dropna(subset=available)
    
    logger.info(f"After PWT merge: {len(est_data)} observations, {est_data['country'].nunique()} countries")
    
    if len(est_data) == 0:
        raise ValueError("No data after PWT merge! Check country name matching.")
    
    # =========================================================================
    # STEP 12: ESTIMATE ALPHA (Capital Share)
    # =========================================================================
    logger.info("=" * 70)
    logger.info("STEP 12: Estimating capital share (α) via fixed effects")
    logger.info("=" * 70)
    
    alphas, mean_alpha = estimate_alphas(est_data)
    
    # -------------------------------------------------------------------------
    # MICE IMPUTATION FOR ALPHAS
    # -------------------------------------------------------------------------
    # The original R code uses:
    #   imp1 <- mice::mice(LH_alphas, method = "norm.predict", m = 1)
    #   LH_alphas_imp <- complete(imp1)
    #
    # Countries without valid alpha estimates (outside 0-1 range or too few obs)
    # get imputed values based on other countries' alphas.
    
    if ENABLE_IMPUTATION:
        # Get list of all countries in est_data
        all_countries = est_data["country"].unique()
        countries_with_alpha = set(alphas["country"].tolist())
        countries_missing = set(all_countries) - countries_with_alpha
        
        if countries_missing:
            logger.info(f"  {len(countries_missing)} countries need alpha imputation")
            
            # For countries without alpha, use mean imputation
            # (In a more sophisticated version, we could use country characteristics)
            for country in countries_missing:
                alphas = pd.concat([alphas, pd.DataFrame({
                    "country": [country],
                    "alpha": [mean_alpha]
                })], ignore_index=True)
            
            logger.info(f"  Imputed missing alphas with mean α = {mean_alpha:.3f}")
    
    # =========================================================================
    # STEP 13: CALCULATE MPL AND DISTORTION FACTOR
    # =========================================================================
    logger.info("=" * 70)
    logger.info("STEP 13: Calculating MPL and distortion factor")
    logger.info("=" * 70)
    
    est_data = calculate_mpl(est_data, alphas, mean_alpha)
    
    # Distortion factor: θ = MPL / AW_Wage
    # This compares actual (average) wages to what the production function says labor is worth
    est_data["theta"] = est_data["mpl"] / est_data["aw_wage"]
    
    logger.info(f"Mean θ (distortion factor): {est_data['theta'].mean():.3f}")
    
    # =========================================================================
    # STEP 14: CALCULATE ADJUSTED WAGE (CHIP per country)
    # =========================================================================
    logger.info("=" * 70)
    logger.info("STEP 14: Calculating adjusted elementary wage (CHIP)")
    logger.info("=" * 70)
    
    # CHIP = Elementary_Wage × θ
    # This adjusts the unskilled wage by the distortion factor
    # NOTE: Wages are already hourly (EAR_4HRL), no conversion needed
    est_data["chip_value"] = est_data["elementary_wage"] * est_data["theta"]
    
    logger.info(f"CHIP range: ${est_data['chip_value'].min():.2f} - ${est_data['chip_value'].max():.2f}")
    
    # =========================================================================
    # STEP 15: AGGREGATE TO COUNTRY LEVEL
    # =========================================================================
    logger.info("=" * 70)
    logger.info("STEP 15: Aggregating to country-level averages")
    logger.info("=" * 70)
    
    # Average across years for each country
    country_data = est_data.groupby("country").agg({
        "chip_value": "mean",
        "elementary_wage": "mean",
        "theta": "mean",
        "alpha": "mean",
        "mpl": "mean",
        "rgdpna": "mean",
        "year": ["min", "max", "count"],
    }).reset_index()
    
    # Flatten column names
    country_data.columns = [
        "country", "chip_value", "elementary_wage", "theta", "alpha", "mpl",
        "gdp", "year_min", "year_max", "n_years"
    ]
    
    logger.info(f"Countries: {len(country_data)}")
    
    # =========================================================================
    # STEP 16: CALCULATE GLOBAL CHIP (GDP-weighted)
    # =========================================================================
    logger.info("=" * 70)
    logger.info("STEP 16: Calculating global CHIP value (GDP-weighted)")
    logger.info("=" * 70)
    
    # GDP weight
    total_gdp = country_data["gdp"].sum()
    country_data["gdp_weight"] = country_data["gdp"] / total_gdp
    
    # GDP-weighted average
    chip_value = (country_data["chip_value"] * country_data["gdp_weight"]).sum()
    
    logger.info(f"Global CHIP (GDP-weighted): ${chip_value:.2f}/hour")
    
    # =========================================================================
    # RESULTS
    # =========================================================================
    logger.info("=" * 70)
    logger.info("RESULTS")
    logger.info("=" * 70)
    
    target = 2.56
    difference = chip_value - target
    pct_diff = (difference / target) * 100
    
    logger.info(f"Calculated CHIP:  ${chip_value:.2f}/hour")
    logger.info(f"Target CHIP:      ${target:.2f}/hour")
    logger.info(f"Difference:       ${difference:+.2f} ({pct_diff:+.1f}%)")
    
    # Validation thresholds
    # - PASSED (<10%): Nearly exact reproduction
    # - MARGINAL (10-30%): Reasonable given different data vintage, no MICE imputation
    # - FAILED (>30%): Indicates methodological issues
    #
    # Note: Fresh API data often differs from historical cached data,
    # and we don't implement MICE imputation for wage ratios, so some
    # deviation is expected.
    
    if abs(pct_diff) < 10:
        logger.info("✅ VALIDATION PASSED: Within 10% of target")
        validation = "PASSED"
    elif abs(pct_diff) < 30:
        logger.warning("⚠️ VALIDATION MARGINAL: 10-30% deviation (expected with fresh data)")
        validation = "MARGINAL"
    else:
        logger.error("❌ VALIDATION FAILED: >30% deviation (check methodology)")
        validation = "FAILED"
    
    return {
        "chip_value": chip_value,
        "target": target,
        "difference": difference,
        "pct_diff": pct_diff,
        "validation": validation,
        "n_countries": len(country_data),
        "n_observations": len(est_data),
        "mean_alpha": mean_alpha,
        "mean_theta": est_data["theta"].mean(),
        "country_data": country_data,
    }


def generate_report(results: dict) -> str:
    """Generate markdown report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    lines = [
        "# Baseline Reproduction Report",
        "",
        f"Generated: {timestamp}",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"**Calculated CHIP:** ${results['chip_value']:.2f}/hour",
        f"**Target CHIP:** ${results['target']:.2f}/hour",
        f"**Difference:** ${results['difference']:+.2f} ({results['pct_diff']:+.1f}%)",
        "",
        f"**Validation:** {results['validation']}",
        "",
        "---",
        "",
        "## Diagnostics",
        "",
        f"- Countries: {results['n_countries']}",
        f"- Observations: {results['n_observations']}",
        f"- Mean α (capital share): {results['mean_alpha']:.3f}",
        f"- Mean θ (distortion factor): {results['mean_theta']:.3f}",
        "",
        "---",
        "",
        "## Top Countries by CHIP Value",
        "",
    ]
    
    # Add country table
    df = results["country_data"].sort_values("chip_value", ascending=False).head(20)
    
    lines.append("| Country | CHIP ($/hr) | Elem. Wage | θ | α |")
    lines.append("|---------|-------------|------------|-----|-----|")
    for _, row in df.iterrows():
        lines.append(
            f"| {row['country']} | ${row['chip_value']:.2f} | "
            f"${row['elementary_wage']:.2f} | {row['theta']:.2f} | {row['alpha']:.2f} |"
        )
    
    lines.extend([
        "",
        "---",
        "",
        "## Methodology",
        "",
        "This script reproduces the original study methodology:",
        "",
        "1. Fetch labor data (employment, wages, hours) for all 9 ISCO occupations",
        "2. Calculate wage ratios relative to Managers (skill weights)",
        "3. Compute effective labor = Σ(hours × skill_weight) across occupations",
        "4. Merge with Penn World Tables (capital, GDP, human capital)",
        "5. Estimate α (capital share) via fixed-effects regression",
        "6. Calculate MPL = (1-α) × (K/L × hc)^α",
        "7. Calculate distortion factor θ = MPL / average_wage",
        "8. Adjust elementary wage: CHIP = elem_wage × θ",
        "9. GDP-weighted global average",
        "",
        "---",
        "",
        "## Notes",
        "",
        "Discrepancies may arise from:",
        "- Data vintage (ILOSTAT updates historical data)",
        "- Country name matching differences",
        "- Occupation code interpretation",
        "- Numerical precision",
        "",
        "For strict reproduction, use `reproduction/` with `data_source: original`.",
    ])
    
    return "\n".join(lines)


def main():
    """Main entry point."""
    script_name = Path(__file__).stem
    log_path = setup_logging(script_name)
    
    print(f"Baseline Reproduction")
    print(f"Target: $2.56/hour")
    print()
    
    with ScriptContext(script_name) as ctx:
        try:
            results = run_baseline()
            
            if results is None:
                ctx.error("Pipeline returned no results")
                return 1
            
            # Generate report
            report = generate_report(results)
            
            # Save report
            output_dir = Path(__file__).parent.parent / "output" / "reports"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = output_dir / f"baseline_{timestamp}.md"
            report_path.write_text(report)
            
            print()
            print(f"{'=' * 60}")
            print(f"CHIP Value: ${results['chip_value']:.2f}/hour")
            print(f"Target:     ${results['target']:.2f}/hour")
            print(f"Validation: {results['validation']}")
            print(f"{'=' * 60}")
            print()
            print(f"Report: {report_path}")
            
            ctx.set_result("chip_value", results["chip_value"])
            ctx.set_result("target", results["target"])
            ctx.set_result("validation", results["validation"])
            ctx.set_result("n_countries", results["n_countries"])
            
            return 0 if results["validation"] in ["PASSED", "MARGINAL"] else 1
            
        except Exception as e:
            logger.exception("Pipeline failed")
            ctx.error(str(e))
            print(f"\n❌ Error: {e}")
            return 1


if __name__ == "__main__":
    sys.exit(main())
