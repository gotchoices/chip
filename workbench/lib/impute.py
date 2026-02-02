"""
Imputation Module

Implements MICE-style imputation for missing values.

The original R study uses:
    mice::mice(data, method = "norm.predict", m = 1)

This is single-imputation using linear regression (OLS) prediction.
We replicate this behavior here.

Design:
    - `norm_predict()` — Linear regression imputation (matches R's norm.predict)
    - `impute_wage_ratios()` — Specific function for wage ratio imputation
    - `impute_alphas()` — Specific function for alpha imputation

Public API:
    norm_predict(df, target_cols) -> pd.DataFrame
    impute_wage_ratios(wage_ratios_df) -> pd.DataFrame
    impute_alphas(alphas_df) -> pd.DataFrame
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


def norm_predict(df: pd.DataFrame, 
                 target_cols: list = None,
                 predictor_cols: list = None) -> pd.DataFrame:
    """
    Impute missing values using linear regression prediction.
    
    This replicates R's mice::mice with method="norm.predict".
    
    For each target column with missing values:
    1. Use rows where target is NOT missing to fit OLS
    2. Use other columns as predictors
    3. Predict missing values
    
    Args:
        df: DataFrame with missing values
        target_cols: Columns to impute (default: all numeric columns with NaN)
        predictor_cols: Columns to use as predictors (default: all other numeric)
        
    Returns:
        DataFrame with missing values imputed
    """
    df = df.copy()
    
    # Identify numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Default: impute all numeric columns with missing values
    if target_cols is None:
        target_cols = [c for c in numeric_cols if df[c].isna().any()]
    
    if not target_cols:
        logger.debug("No columns to impute")
        return df
    
    # For each target column
    for target in target_cols:
        missing_mask = df[target].isna()
        n_missing = missing_mask.sum()
        
        if n_missing == 0:
            continue
        
        # Determine predictors (other numeric columns)
        if predictor_cols is None:
            available_predictors = [c for c in numeric_cols if c != target]
        else:
            available_predictors = [c for c in predictor_cols if c != target]
        
        if not available_predictors:
            # No predictors - use mean imputation as fallback
            mean_val = df[target].mean()
            df.loc[missing_mask, target] = mean_val
            logger.debug(f"Imputed {n_missing} values in '{target}' using mean ({mean_val:.4f})")
            continue
        
        # Get complete cases for training
        train_mask = ~missing_mask
        for pred in available_predictors:
            train_mask &= df[pred].notna()
        
        if train_mask.sum() < 3:
            # Not enough data - use mean
            mean_val = df[target].mean()
            df.loc[missing_mask, target] = mean_val
            logger.debug(f"Imputed {n_missing} values in '{target}' using mean (insufficient training data)")
            continue
        
        # Prepare training data
        X_train = df.loc[train_mask, available_predictors].values
        y_train = df.loc[train_mask, target].values
        
        # OLS: y = X @ beta
        # Add intercept column
        X_train_const = np.column_stack([np.ones(len(X_train)), X_train])
        
        try:
            # Solve normal equations: beta = (X'X)^-1 X'y
            beta = np.linalg.lstsq(X_train_const, y_train, rcond=None)[0]
            
            # Prepare prediction data (rows with missing target)
            # For prediction, we need all predictor values
            pred_mask = missing_mask.copy()
            for pred in available_predictors:
                pred_mask &= df[pred].notna()
            
            if pred_mask.sum() == 0:
                # Can't predict - use mean
                mean_val = df[target].mean()
                df.loc[missing_mask, target] = mean_val
                logger.debug(f"Imputed {n_missing} values in '{target}' using mean (missing predictors)")
                continue
            
            X_pred = df.loc[pred_mask, available_predictors].values
            X_pred_const = np.column_stack([np.ones(len(X_pred)), X_pred])
            
            # Predict
            y_pred = X_pred_const @ beta
            
            # Fill in predictions
            df.loc[pred_mask, target] = y_pred
            
            # For rows where we couldn't predict (missing predictors), use mean
            still_missing = df[target].isna()
            if still_missing.sum() > 0:
                mean_val = df[target].mean()
                df.loc[still_missing, target] = mean_val
            
            logger.debug(f"Imputed {pred_mask.sum()} values in '{target}' using OLS, "
                        f"{still_missing.sum()} using mean")
            
        except Exception as e:
            # Fallback to mean
            mean_val = df[target].mean()
            df.loc[missing_mask, target] = mean_val
            logger.warning(f"OLS imputation failed for '{target}': {e}, using mean")
    
    return df


def impute_wage_ratios(wage_ratios: pd.DataFrame,
                       country_col: str = "country",
                       occupation_cols: list = None) -> pd.DataFrame:
    """
    Impute missing wage ratios using linear regression.
    
    Matches the original R code:
        wageratdata %>%
          group_by(Country) %>%
          summarise(across(c(2:9), ~ mean(.x, na.rm = TRUE)))
        imp <- mice::mice(wageratdata, method = "norm.predict", m = 1)
    
    Args:
        wage_ratios: DataFrame with country and occupation wage ratio columns
        country_col: Name of country column
        occupation_cols: List of occupation columns to impute
        
    Returns:
        DataFrame with imputed wage ratios
    """
    df = wage_ratios.copy()
    
    # Default occupation columns
    if occupation_cols is None:
        occupation_cols = [c for c in df.columns 
                          if c not in [country_col, "year"] 
                          and df[c].dtype in [np.float64, np.int64, float, int]]
    
    # Count missing before
    missing_before = df[occupation_cols].isna().sum().sum()
    
    if missing_before == 0:
        logger.info("No missing wage ratios to impute")
        return df
    
    # Apply norm_predict imputation
    # Use only the numeric columns for imputation
    numeric_df = df[occupation_cols].copy()
    imputed_numeric = norm_predict(numeric_df, target_cols=occupation_cols)
    
    # Put back into original dataframe
    df[occupation_cols] = imputed_numeric
    
    # Count missing after
    missing_after = df[occupation_cols].isna().sum().sum()
    
    logger.info(f"Imputed wage ratios: {missing_before} missing -> {missing_after} missing")
    
    return df


def impute_alphas(alphas: pd.DataFrame,
                  country_col: str = "country",
                  alpha_cols: list = None) -> pd.DataFrame:
    """
    Impute missing alpha (capital share) values using linear regression.
    
    Matches the original R code:
        imp1 <- mice::mice(LH_alphas, method = "norm.predict", m = 1)
        LH_alphas_imp <- complete(imp1)
    
    Args:
        alphas: DataFrame with country and alpha columns
        country_col: Name of country column  
        alpha_cols: List of alpha columns to impute (default: columns containing 'alpha')
        
    Returns:
        DataFrame with imputed alphas
    """
    df = alphas.copy()
    
    # Default: find alpha columns
    if alpha_cols is None:
        alpha_cols = [c for c in df.columns 
                     if 'alpha' in c.lower() 
                     and df[c].dtype in [np.float64, np.int64, float, int]]
    
    if not alpha_cols:
        logger.warning("No alpha columns found to impute")
        return df
    
    # Count missing before
    missing_before = df[alpha_cols].isna().sum().sum()
    
    if missing_before == 0:
        logger.info("No missing alphas to impute")
        return df
    
    # For alpha imputation, we may have characteristics to use as predictors
    # The R code uses the alphas themselves as predictors for each other
    # We'll do the same - use other alpha columns as predictors
    
    for alpha_col in alpha_cols:
        other_alphas = [c for c in alpha_cols if c != alpha_col]
        
        if other_alphas:
            # Use other alphas as predictors
            df = norm_predict(df, target_cols=[alpha_col], predictor_cols=other_alphas)
        else:
            # Single alpha column - use mean
            missing_mask = df[alpha_col].isna()
            if missing_mask.sum() > 0:
                mean_val = df[alpha_col].mean()
                df.loc[missing_mask, alpha_col] = mean_val
    
    # Count missing after
    missing_after = df[alpha_cols].isna().sum().sum()
    
    logger.info(f"Imputed alphas: {missing_before} missing -> {missing_after} missing")
    
    return df
