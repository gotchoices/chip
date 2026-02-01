# Global Aggregation and Weighting Schemes

*Analysis of how country-level CHIP values should be combined into a single global rate.*

---

## Table of Contents

1. [Introduction](#1-introduction)
   - 1.1 The Aggregation Problem
   - 1.2 Why Weighting Matters
2. [Weighting Schemes](#2-weighting-schemes)
   - 2.1 GDP-Weighted (Original Study)
   - 2.2 Labor-Force Weighted
   - 2.3 Unweighted (Equal Countries)
   - 2.4 PPP-Adjusted Variants
3. [Philosophical Considerations](#3-philosophical-considerations)
   - 3.1 "One Hour = One Hour" Across Borders?
   - 3.2 Economic Significance vs. Human Significance
   - 3.3 Alignment with CHIP Definition
4. [Empirical Comparison](#4-empirical-comparison)
   - 4.1 Sensitivity of Results to Weighting Choice
   - 4.2 Country-Level Contributions
   - 4.3 Developed vs. Developing Balance
5. [Recommendations](#5-recommendations)
6. [References](#6-references)

---

## 1. Introduction

### 1.1 The Aggregation Problem

The CHIP is defined as the value of one hour of nominal unskilled labor in a hypothetical global free market. But we don't observe a single global market—we observe distinct national labor markets with vastly different wage levels.

The original study calculates a distortion-adjusted wage for elementary workers in each of 89 countries. These country-level values range from approximately $0.05/hour (Rwanda) to $8/hour (Italy). The **aggregation problem** is: how do we combine these disparate values into a single global CHIP rate?

This is not a purely technical question. The choice of aggregation method embeds assumptions about what the CHIP should represent and whose labor matters most in defining the global baseline.

### 1.2 Why Weighting Matters

Different weighting schemes can yield materially different results. Consider a simplified example with two countries:

| Country | Population | GDP | Unskilled Wage |
|---------|------------|-----|----------------|
| A (rich) | 100M | $10T | $15/hour |
| B (poor) | 1B | $2T | $1/hour |

| Weighting Method | Calculation | Result |
|-----------------|-------------|--------|
| GDP-weighted | (10/12)×$15 + (2/12)×$1 | **$12.67** |
| Labor-weighted | (100/1100)×$15 + (1000/1100)×$1 | **$2.27** |
| Unweighted | ($15 + $1) / 2 | **$8.00** |

The range is enormous: $2.27 to $12.67, depending solely on how we weight the countries. This is not a rounding error—it's a fundamental methodological choice that requires justification.

---

## 2. Weighting Schemes

### 2.1 GDP-Weighted (Original Study)

The original study uses **GDP weighting**: each country's CHIP value is weighted by its share of total GDP among the countries in the sample.

$$CHIP_{GDP} = \sum_j \left( w^*_j \cdot \frac{GDP_j}{\sum_k GDP_k} \right)$$

**Rationale:**
- Larger economies have more economic activity, hence more "transactions" at the CHIP rate
- Productive economies may better approximate "efficient" markets
- Aligns with how economists often weight international comparisons

**Effect:**
- Emphasizes developed economies (US, EU, Japan, China)
- Produces a higher CHIP value than alternatives
- Original study result: **$2.53/hour**

### 2.2 Labor-Force Weighted

An alternative is **labor-force weighting**: each country weighted by its number of unskilled workers.

$$CHIP_{Labor} = \sum_j \left( w^*_j \cdot \frac{L_j}{\sum_k L_k} \right)$$

**Rationale:**
- "One worker's hour is one worker's hour" regardless of nationality
- Democratic: each person counts equally
- Reflects where unskilled workers actually are (predominantly developing countries)

**Effect:**
- Emphasizes developing economies (India, Indonesia, Nigeria, Bangladesh)
- Produces a lower CHIP value than GDP weighting
- Gives voice to the global majority of unskilled workers

### 2.3 Unweighted (Equal Countries)

The simplest approach: **unweighted average** where each country counts equally.

$$CHIP_{Unweighted} = \frac{1}{N} \sum_j w^*_j$$

**Rationale:**
- Treats each national market as an independent observation
- Avoids assumptions about which countries "matter more"
- Simple and transparent

**Effect:**
- Highly sensitive to sample composition (small countries count as much as large)
- Vulnerable to outliers
- May over-represent small wealthy nations (Luxembourg, Singapore) or small poor ones

### 2.4 PPP-Adjusted Variants

All schemes above can be computed using:
- **Nominal USD wages** (market exchange rates)
- **PPP-adjusted wages** (purchasing power parity)

PPP adjustment attempts to equalize buying power across countries. A $2 wage in India buys more than $2 in the US. PPP-adjusted values are typically higher for developing countries.

**Trade-off:**
- Nominal: What you'd actually receive if paid in dollars
- PPP: What your wage is "worth" in local purchasing power

The CHIP definition refers to a "worldwide market"—this suggests nominal values (what labor would trade for globally). But PPP captures local welfare better.

---

## 3. Philosophical Considerations

### 3.1 "One Hour = One Hour" Across Borders?

A core question: in a hypothetical borderless global market, would one hour of unskilled labor in Bangladesh trade at the same rate as one hour in Germany?

**Arguments for equal valuation:**
- The CHIP definition specifies identical work characteristics (minimal training, no special skills)
- In a truly free market, wage arbitrage would equalize rates
- The definition explicitly removes borders and distortions

**Arguments against:**
- Even identical labor may have different productivity in different contexts (infrastructure, institutions)
- Migration costs mean labor isn't truly fungible
- "Effective" labor quality may vary (nutrition, health, education even at "unskilled" level)

The original study's distortion factor approach attempts to adjust for market frictions, but doesn't fully resolve whether geographic wage differences are "distortions" or "fundamentals."

### 3.2 Economic Significance vs. Human Significance

Weighting schemes embed a values choice:

**GDP weighting** privileges **economic significance**:
- Markets where more economic activity occurs
- Where more value is transacted
- Implicitly: where labor "matters more" economically

**Labor-force weighting** privileges **human significance**:
- Each worker's hour counts equally
- Democratic representation of the global workforce
- Implicitly: CHIP should reflect the median worker's reality

Neither is objectively correct. The choice depends on what the CHIP is *for*:
- If CHIP is a unit for global commerce, GDP weighting may be appropriate
- If CHIP is meant to represent "typical" human labor value, labor-force weighting may be better

### 3.3 Alignment with CHIP Definition

The [canonical CHIP definition](https://gotchoices.org/mychips/definition.html) states:

> "...how an hour of nominal, unskilled labor might be valued in a hypothetical worldwide, free, and balanced market where there are no borders, tariffs, or other distortions."

Key phrases:
- **"Worldwide"** — suggests a single global value, not a weighted average
- **"Free and balanced market"** — implies equilibrium, but doesn't specify weighting
- **"No borders"** — suggests labor mobility, which would equalize wages

**Interpretation:** The definition imagines a world where labor can flow freely. In such a world, wage differences would compress through migration. The resulting equilibrium wage might be *between* current developed and developing rates—closer to labor-weighted than GDP-weighted, but not identical to either.

The definition doesn't resolve the weighting question, but it does suggest the answer isn't simply "weight by current economic power."

---

## 4. Empirical Comparison

> **⚠️ PENDING DATA**
> 
> This section requires numerical results from the Python reproduction work. Once complete, it will include:

### 4.1 Sensitivity of Results to Weighting Choice

*[To be populated with: CHIP values under each weighting scheme, with percentage differences]*

### 4.2 Country-Level Contributions

*[To be populated with: Table showing which countries contribute most under each scheme]*

### 4.3 Developed vs. Developing Balance

*[To be populated with: Analysis of how much of the final value comes from developed vs. developing nations under each scheme]*

---

## 5. Recommendations

### 5.1 Report Multiple Values

Given the sensitivity to weighting choice and the philosophical ambiguity, we recommend **reporting the CHIP value under multiple weighting schemes** rather than privileging one:

| Scheme | Interpretation |
|--------|---------------|
| GDP-weighted | "Economic activity" weighted value |
| Labor-force weighted | "Democratic" or "median worker" value |
| Unweighted | Simple average (sensitivity check) |

Transparency about methodology is more valuable than false precision in a single number.

### 5.2 Consider a "Preferred" Range

Rather than a point estimate, consider reporting a range:

> "The global CHIP value is estimated at **$X.XX to $Y.YY per hour**, depending on weighting methodology."

This acknowledges methodological uncertainty while still providing actionable guidance.

### 5.3 Document the Choice

If a single value must be used for practical purposes, document:
1. Which weighting scheme was chosen
2. Why that scheme was selected
3. How much the result would differ under alternatives

### 5.4 Future Consideration: Hybrid Approaches

More sophisticated approaches could be explored:
- **Geometric mean** of GDP and labor-weighted values
- **Trimmed means** to reduce outlier sensitivity
- **Regional weighting** (weight regions equally, then countries within regions)

These may better balance competing concerns than any single simple scheme.

---

## 6. References

Bateman, K. (2022). *Got Choices*. https://gotchoices.org

International Labour Organization. ILOSTAT Database. https://ilostat.ilo.org

Feenstra, R.C., Inklaar, R., & Timmer, M.P. (2015). The Next Generation of the Penn World Table. *American Economic Review*, 105(10): 3150-3182.

---

*Document status: SECTIONS 1-3, 5-6 COMPLETE — Section 4 pending reproduction data*
