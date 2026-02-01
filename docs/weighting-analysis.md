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
   - 3.2 The Practical Purpose of CHIP
   - 3.3 GDP Weighting as a "Frictionless" Proxy
   - 3.4 Economic Freedom Indices: A Direct Measure?
   - 3.5 Alignment with CHIP Definition
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

### 3.2 The Practical Purpose of CHIP

Before debating weighting schemes philosophically, we should clarify what the CHIP is *for*.

The CHIP serves primarily as an **index for the MyCHIPs system**—a practical reference point that helps users understand how much value they're receiving in CHIP units compared to their native currency. A user in Mexico receiving 10 CHIPs needs to know roughly what that means in pesos.

This practical purpose argues **against** publishing multiple aggregation values. Users need a single, clear reference rate—not a range that introduces confusion. The goal is a defensible single number, not an academic exploration of all possible values.

### 3.3 GDP Weighting as a "Frictionless" Proxy

The original study used GDP weighting with a specific rationale beyond "larger economies matter more":

**Premise:** The CHIP definition imagines a frictionless global economy. Economies with fewer frictions tend to be more productive, and more productive economies have larger GDPs. Therefore, GDP weighting implicitly emphasizes economies that are *closer to the frictionless ideal*.

This is an elegant argument:
- Free markets → higher productivity → larger GDP
- Weighting by GDP → emphasizing markets that better approximate the CHIP's theoretical ideal
- The CHIP value then reflects what labor is worth in the *most efficient* markets, extrapolated globally

**Concern:** The correlation between GDP and "frictionlessness" is imperfect. China has a massive GDP but significant market distortions. Some small, highly free economies (Singapore, Hong Kong) are underweighted relative to their market efficiency.

### 3.4 Economic Freedom Indices: A Direct Measure?

Rather than using GDP as a *proxy* for frictionlessness, we could directly measure it.

**Available indices:**

| Index | Source | Coverage |
|-------|--------|----------|
| Index of Economic Freedom | Heritage Foundation | 180+ countries |
| Economic Freedom of the World | Fraser Institute | 160+ countries |
| Ease of Doing Business | World Bank | 190 countries |

These indices measure exactly what the CHIP definition cares about: how free a market is from distortions, regulations, and barriers.

**Potential approach: Freedom-weighted aggregation**

$$CHIP_{Freedom} = \sum_j \left( w^*_j \cdot \frac{Freedom_j}{\sum_k Freedom_k} \right)$$

Countries with freer markets (higher index scores) get more weight, directly operationalizing the CHIP definition's "free and balanced market" requirement.

**Interesting note:** The original study *downloaded* the Heritage Foundation Economic Freedom Index (`freedomindex.xlsx`) but did not use it in the final analysis. This suggests the researchers considered this approach.

**Potential refinement: Freedom × GDP weighting**

A hybrid approach could weight by the *product* of economic freedom and GDP:

$$CHIP_{Hybrid} = \sum_j \left( w^*_j \cdot \frac{Freedom_j \times GDP_j}{\sum_k Freedom_k \times GDP_k} \right)$$

This emphasizes economies that are *both* large and free—arguably the best available proxy for the hypothetical frictionless global market.

### 3.5 Alignment with CHIP Definition

The [canonical CHIP definition](https://gotchoices.org/mychips/definition.html) states:

> "...how an hour of nominal, unskilled labor might be valued in a hypothetical worldwide, free, and balanced market where there are no borders, tariffs, or other distortions."

Key phrases and implications:
- **"Worldwide"** — a single global value is needed
- **"Free and balanced market"** — emphasis on efficiency, not democracy
- **"No borders, tariffs, or distortions"** — the ideal is a frictionless market

**Interpretation:** The definition emphasizes *market freedom*, not equal representation of workers. This supports weighting schemes that emphasize economies closer to the frictionless ideal—whether measured by GDP (as a proxy) or directly by economic freedom indices.

The definition's focus on a "free" market suggests that GDP weighting (or freedom weighting) is more aligned than labor-force weighting, which would give equal voice to highly distorted markets.

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

### 5.1 A Single Value is Required

For practical use in MyCHIPs, users need a **single, clear CHIP reference rate**—not a range of values that introduces confusion. The goal is to find the most defensible single number.

### 5.2 GDP Weighting is Reasonable

The original study's GDP weighting approach is defensible:
- It serves as a proxy for "frictionless" markets (freer → more productive → larger GDP)
- It aligns with the CHIP definition's emphasis on a "free and balanced market"
- It produces a plausible result ($2.53/hour)

For continuity, GDP weighting remains a reasonable default.

### 5.3 Explore Economic Freedom Weighting

A potentially superior approach would weight by **economic freedom indices** directly:
- More theoretically aligned with the CHIP definition's "free market" requirement
- Avoids conflating market size with market efficiency
- Data is available (Heritage Foundation, Fraser Institute)

**Recommended exploration:**
1. Calculate CHIP value using freedom-weighted aggregation
2. Calculate CHIP value using freedom × GDP hybrid weighting
3. Compare to GDP-only weighting
4. Assess whether the additional complexity is justified by improved alignment

### 5.4 Document Methodology Transparently

Whichever weighting scheme is adopted, documentation should include:
1. The chosen method and its rationale
2. Sensitivity analysis showing how results vary under alternatives
3. Acknowledgment that the choice involves judgment

### 5.5 Research Questions for Empirical Work

The reproduction work should answer:
1. How different is freedom-weighted from GDP-weighted?
2. Does the Heritage Index correlate strongly with GDP? (If so, the approaches may converge)
3. Which specific countries drive the differences?

---

## 6. References

Bateman, K. (2022). *Got Choices*. https://gotchoices.org

International Labour Organization. ILOSTAT Database. https://ilostat.ilo.org

Feenstra, R.C., Inklaar, R., & Timmer, M.P. (2015). The Next Generation of the Penn World Table. *American Economic Review*, 105(10): 3150-3182.

---

*Document status: SECTIONS 1-3, 5-6 COMPLETE — Section 4 pending reproduction data*
