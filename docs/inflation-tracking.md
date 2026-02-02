# CHIP Value and Currency Inflation: A Predictive Analysis

## Purpose

This paper analyzes whether the CHIP valuation methodology should track currency inflation over time, examines why the original study used a GDP deflator, and proposes alternative approaches better suited to the MyCHIPs use case.

---

## 1. Introduction

### 1.1 The Core Question
If world currencies inflate over time, should we expect the CHIP value (expressed in USD) to increase, decrease, or remain stable?

### 1.2 Why This Matters
- **For MyCHIPs users**: The CHIP estimate helps users understand the value of pledges denominated in CHIPs
- **For methodology validation**: Proper inflation behavior validates the wage-based approach
- **For practical implementation**: Determines whether CHIP naturally hedges against currency devaluation

### 1.3 The MyCHIPs Use Case
When someone receives a CHIP-denominated pledge (IOU) in MyCHIPs, they need to understand what that pledge is worth in their native currency. The CHIP estimator serves this purpose.

---

## 2. Philosophical Foundation: Labor as the Universal Index

### 2.1 The Problem with Fiat Currency
All fiat currencies are subject to inflation, manipulation, and instability. There is no "natural unit" for measuring value — every value is expressed as a multiple of some other value.

### 2.2 Alternative Approaches
- **Basket of goods**: Some alternative currencies use a fixed basket of commodities as an inflation-proof index
- **Gold standard**: Precious metals provide stability but are subject to manipulation and supply constraints

### 2.3 The CHIP Theory: Labor as the Index of All Value
The CHIP approach posits that **nominal unskilled labor** constitutes the ultimate "index of all goods and services" because:

1. **All goods and services are ultimately produced by labor** — labor is the fundamental input
2. **Labor is universal** — every person has their own supply
3. **Labor is resistant to manipulation** — unlike gold or fiat currency
4. **Labor scales with population** — naturally grows with the economy

### 2.4 The CHIP Definition
One CHIP = one hour of nominal unskilled labor in a frictionless global economy.

Key word: **nominal** — not adjusted for inflation.

---

## 3. The Original Study's Methodology

### 3.1 Core Calculation
The study calculates:
```
CHIP = Elementary_Wage × Distortion_Factor
     = Elementary_Wage × (MPL / Actual_Wage)
```

Where:
- **Elementary_Wage**: Observed hourly wage for ISCO "Elementary Occupations"
- **MPL**: Marginal Product of Labor from Cobb-Douglas estimation
- **Distortion_Factor (θ)**: Ratio adjusting for market frictions

### 3.2 Key Methodological Features
1. **Deflation to base year**: Wages are deflated using GDP deflator to constant 2017 dollars
2. **GDP-weighted aggregation**: Countries weighted by economic output
3. **Cross-year pooling**: Data from multiple years (roughly 2002-2019) averaged together

### 3.3 How the Deflator Works
The GDP deflator converts nominal values to real (constant-dollar) values:

```
Real Wage (2017$) = Nominal Wage / (Deflator_year / Deflator_2017)
```

Example:
- A $10 wage in 2005 becomes ~$11.76 in 2017 dollars
- A $15 wage in 2019 becomes ~$13.89 in 2017 dollars
- These can now be meaningfully compared and averaged

### 3.4 Why an Economist Would Deflate

The original study pools data from multiple years. From an econometric standpoint:

| Problem | Deflation Solution |
|---------|-------------------|
| Can't average $10 (2005) with $15 (2019) | Convert both to 2017 dollars |
| Fixed-effects regression needs comparable units | Deflation provides that |
| Time-series comparability | Standard academic practice |

**Deflation is reflexive for economists doing cross-temporal analysis** — it's the "correct" approach for academic time-series work.

### 3.5 The Result and Its Interpretation

The $2.56 result means: **"One CHIP is worth $2.56 in 2017 dollars."**

To get today's value, you would multiply:
```
Nominal CHIP (2026) = $2.56 × (Deflator_2026 / Deflator_2017)
```

If inflation has been ~25% since 2017, that's roughly $3.20 in 2026 nominal dollars.

---

## 4. The Mismatch: Academic vs. Practical Goals

### 4.1 What the Study Answers
"What is the average real CHIP value across 2002-2019?"

### 4.2 What MyCHIPs Needs
"What is one CHIP worth in dollars **right now**?"

### 4.3 The Fundamental Mismatch

| Econometric Goal | MyCHIPs Goal |
|------------------|--------------|
| Compare values across time | Know today's price |
| Pool data for statistical power | Use current market conditions |
| Produce "timeless" real estimate | Produce actionable nominal value |
| Academic publication | Practical wallet interface |

### 4.4 User Experience Problem
When a MyCHIPs user receives a pledge for "10 CHIPs", they want to know: **How many dollars is that worth today?**

If CHIP is deflated to 2017 dollars:
- The user must find the current deflator index
- Multiply the CHIP value by the deflator
- This adds complexity and potential for error

### 4.5 The Deflator as a Contextual Error
The original study applied deflation correctly **for academic purposes**, but this conflicts with the **intended practical use case**.

Per the CHIP definition, one CHIP equals one hour of **nominal** unskilled labor. If labor costs $3/hour today, CHIP = $3. If labor costs $4/hour next year, CHIP = $4.

The deflator **removes** this natural inflation tracking — arguably a core feature, not a bug.

---

## 5. Expected Behavior Without Deflation

### 5.1 Natural Inflation Tracking
If we remove deflation from the methodology:
- CHIP should **increase** as currencies inflate
- CHIP should **track nominal labor costs**
- CHIP serves as a natural hedge against currency devaluation
- One CHIP always equals "one hour of unskilled labor at current prices"

### 5.2 Real Economic Changes
Even in nominal terms, CHIP could change due to real economic factors:
- **Productivity gains**: If workers become more productive, MPL increases
- **Globalization**: Integration of low-wage countries into global markets
- **Automation**: Reducing demand for unskilled labor
- **Education**: Shifting composition of the workforce

### 5.3 The CHIP Philosophy on Real Changes
The CHIP theory accepts that labor value drifts relative to other commodities. This is expected:
- Every commodity value drifts relative to every other
- There is no absolute unit of value
- CHIP is simply **more stable** than fiat currency, not perfectly stable

### 5.4 Distinguishing Signal from Noise

| Change Type | Cause | Acceptable? |
|-------------|-------|-------------|
| Nominal increase | Currency inflation | Yes (expected) |
| Real decrease | Productivity gains outpacing wages | Yes (economic reality) |
| Composition shift | Different countries in sample | No (methodological artifact) |

---

## 6. Alternative Methodological Approaches

### 6.1 Simple Approach: Most Recent Year Only
Instead of pooling and deflating across years:

1. Use only the most recent year with complete data (e.g., 2024)
2. No deflation needed — single year is already in current dollars
3. Update periodically with fresh data

**Advantages**: Simple, no deflation complexity, directly answers "what is CHIP worth today?"

**Disadvantages**: More volatile, dependent on single year's data quality

### 6.2 Windowed Average: Centered Window
Calculate CHIP for a target year using adjacent years, inflation-adjusted to the target:

```
CHIP(2019) = Average of:
  - 2018 data × (Deflator_2019 / Deflator_2018)  → adjusted to 2019$
  - 2019 data × 1.0                              → already 2019$
  - 2020 data × (Deflator_2019 / Deflator_2020)  → adjusted to 2019$
```

**Advantages**: Smooths year-to-year volatility, all values expressed in target year's dollars

**Key insight**: Deflation is used for comparability **within the window**, but the result is in **target year nominal dollars** — not a fixed base year.

### 6.3 Windowed Average: Trailing Window
Use only past data to avoid forward-looking bias:

```
CHIP(2019) = Average of:
  - 2017 data × (Deflator_2019 / Deflator_2017)
  - 2018 data × (Deflator_2019 / Deflator_2018)
  - 2019 data × 1.0
```

**Advantages**: Available immediately (no waiting for future data), conservative

**Disadvantages**: Lags current conditions

### 6.4 Sliding Time Series
Apply windowing to each year, producing a time series:

| Year | Window | Result (Nominal) |
|------|--------|------------------|
| 2017 | 2015-2017 | $2.30 (2017$) |
| 2018 | 2016-2018 | $2.45 (2018$) |
| 2019 | 2017-2019 | $2.60 (2019$) |
| 2020 | 2018-2020 | $2.75 (2020$) |

This produces a nominal time series that should track inflation.

### 6.5 Comparison of Approaches

| Approach | Volatility | Lag | Complexity | Result Units |
|----------|------------|-----|------------|--------------|
| Single year | High | None | Low | Nominal (current) |
| Centered window | Low | Some | Medium | Nominal (target year) |
| Trailing window | Low | More | Medium | Nominal (target year) |
| Original (pooled, deflated) | Very low | High | Medium | Real (base year) |

---

## 7. Recommendations

### 7.1 For the CHIP Estimator (MyCHIPs Use)
1. **Remove fixed-base deflation** from the core calculation
2. Express CHIP in **nominal current-year dollars**
3. Use **trailing windowed average** (3-5 years) for stability
4. Report the **year** of the estimate clearly
5. Update annually with fresh data

### 7.2 For Academic Analysis
1. Continue to provide deflated (real) values as supplementary information
2. Hold country sample constant when comparing across years
3. Report both nominal and real values for transparency

### 7.3 For MyCHIPs Implementation
1. Publish CHIP value with clear date stamp (e.g., "CHIP 2024: $3.15")
2. Update periodically (annually) with fresh data
3. Communicate that CHIP tracks labor costs, which includes inflation
4. Optionally show trend: "Up 3% from last year"

---

## 8. Preliminary Empirical Evidence

### 8.1 Test Methodology
Using the reproduction pipeline with `data_source: "original"`, we calculated CHIP values for different time windows, all deflated to 2017 dollars per the original methodology.

### 8.2 Results

| Period | CHIP Value (2017$) | Countries in Sample |
|--------|-------------------|---------------------|
| **1992-2019 (baseline)** | **$2.56** | **90** |
| 2006-2008 | $0.98 | 27 |
| 2010-2012 | $1.42 | 38 |
| 2014-2016 | $1.91 | 57 |
| 2017-2019 | $1.74 | 62 |

*Note: The baseline ($2.56) matches the reproduction of the original study. It uses all available data from 1992-2019, resulting in more countries and cross-year averaging.*

### 8.3 Observations

1. **Rising trend in deflated terms**: CHIP nearly doubled from $0.98 (2006-08) to $1.91 (2014-16), even after deflation. However, this does NOT necessarily mean real wages rose.

2. **Composition effect dominates**: The country count tripled (27 → 57 → 62). The rise and subsequent fall likely reflects **which countries are in the sample**, not wage trends:
   - Early periods: Fewer countries with complete data (likely wealthier nations with better statistical infrastructure)
   - Middle periods: More countries added — possibly higher-wage countries expanding their reporting
   - Latest period: Even more countries — likely lower-wage developing nations catching up on data availability

3. **The deflator worked correctly**: If inflation were the cause, the deflated values would be stable. The volatility confirms deflation is removing price-level effects — what remains is composition and/or real economic change.

4. **Key insight**: To isolate real wage trends from composition effects, we would need to hold the country sample constant across all periods.

5. **Aggregation sensitivity**: The full-range CHIP ($2.56) is significantly higher than the average of individual periods (~$1.51). This suggests:
   - High-wage countries may have data in years not covered by narrow windows
   - The Cobb-Douglas estimation behaves differently with more pooled observations
   - GDP weighting amplifies contributions from countries with intermittent data availability
   - **The methodology is sensitive to window selection and data completeness**

### 8.4 Implications

- **The deflator is masking some of the expected behavior** — in nominal terms, CHIP increases would be more pronounced
- **Country composition is a confounding factor** — a proper methodology should either:
  - Hold country sample constant across periods
  - Weight by consistent GDP shares
- **The 2017-2019 drop deserves investigation** — is it real wage stagnation or sample composition?

### 8.5 Testable Hypotheses

Based on this analysis, we propose the following hypotheses for empirical testing in a subsequent modeling project:

**H1: Nominal CHIP tracks inflation**
> If we calculate CHIP without deflation (nominal terms), the value should increase over time, roughly tracking CPI or GDP deflator indices.

**H2: Deflated CHIP is stable when composition is controlled**
> If we hold the country sample constant across all periods, deflated CHIP values should be relatively stable, reflecting only real economic changes (not inflation or composition effects).

**H3: Windowed averaging produces coherent time series**
> A trailing-window methodology (e.g., 3-year rolling average, inflation-adjusted to target year) should produce a smooth, interpretable time series of nominal CHIP values.

**H4: Recent-year CHIP is more actionable for MyCHIPs**
> A nominal CHIP calculated from recent data (e.g., 2022-2024) will be more useful for MyCHIPs users than the current deflated, all-years-pooled approach.

### 8.6 Next Steps for Validation
1. Create `estimates/` project with modified pipeline (no fixed-base deflation)
2. Implement trailing window methodology
3. Hold country sample constant to test H2
4. Compare nominal CHIP trend to official inflation benchmarks (H1)
5. Produce sliding time series to test H3

---

## 9. Conclusions

### 9.1 Summary of Findings
1. **The deflator was appropriate for academic analysis** but not for MyCHIPs practical use
2. **CHIP should track inflation** — this is a feature, not a bug
3. **Nominal CHIP** is more appropriate for practical value estimation
4. **Windowed approaches** provide stability while maintaining current-year relevance

### 9.2 The Path Forward
This analysis motivates a new project:
- Create an `estimates/` folder for forward-looking CHIP estimation
- Implement trailing window methodology
- Produce nominal, current-year CHIP values
- Validate against inflation benchmarks

### 9.3 The CHIP Value Proposition
By anchoring to labor rather than a basket of goods or precious metals:
- CHIP provides a stable, manipulation-resistant unit of value
- CHIP naturally tracks the cost of living (since labor buys goods)
- CHIP is universally accessible (everyone can work)

---

## References

- CHIP Definition: https://gotchoices.org/mychips/definition.html
- Original CHIP valuation study (see `original/README.md`)
- FRED GDP Deflator: USAGDPDEFAISMEI
- ILO Global Wage Reports
- [Additional references as needed]
