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
   - 2.4 Freedom-Weighted (Heritage Foundation)
   - 2.5 HDI-Weighted (UNDP)
   - 2.6 PPP-Adjusted Variants
3. [Philosophical Considerations](#3-philosophical-considerations)
   - 3.1 "One Hour = One Hour" Across Borders?
   - 3.2 The Practical Purpose of CHIP
   - 3.3 GDP Weighting as a "Frictionless" Proxy
   - 3.4 Economic Freedom Indices: A Direct Measure?
   - 3.5 Alignment with CHIP Definition
4. [Empirical Comparison](#4-empirical-comparison)
   - 4.1 Five Schemes, Five Answers
   - 4.2 Elimination by Reasoning
   - 4.3 GDP vs HDI: The Final Question
   - 4.4 Addressing the Circularity Concern
   - 4.5 Country Multipliers
5. [Recommendations](#5-recommendations)
   - 5.1 Use GDP-Weighted Aggregation
   - 5.2 Publish the Full Range for Transparency
   - 5.3 Publish Country Multipliers
   - 5.4 Acknowledge the Philosophical Nature of the Choice
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

### 2.4 Freedom-Weighted (Heritage Foundation)

Weight each country by the product of its GDP and its Heritage Foundation
*Index of Economic Freedom* score, directly operationalizing the CHIP
definition's "free and balanced market" requirement.

$$CHIP_{Freedom} = \sum_j \left( w^*_j \cdot \frac{Freedom_j \times GDP_j}{\sum_k Freedom_k \times GDP_k} \right)$$

**Rationale:**
- Measures market freedom directly rather than using GDP as a proxy
- Emphasizes economies that are both large and free
- Available for 180+ countries, scored 0–100

**Effect:**
- Strongly correlates with GDP per capita, amplifying rich-country weight
- Produces the *highest* CHIP of the five schemes tested ($2.85)
- USA alone holds 27% of the weight
- Relies on a single think tank's editorial judgments

### 2.5 HDI-Weighted (UNDP)

Weight each country by its Human Development Index (health, education,
income), reflecting the idea that developed economies with high standards
of living better approximate the free-market wage equilibrium.

$$CHIP_{HDI} = \sum_j \left( w^*_j \cdot \frac{HDI_j}{\sum_k HDI_k} \right)$$

**Rationale:**
- "Standard of living" captures how much workers benefit from their economy
- Politically neutral, widely respected composite index
- In a free market, countries would converge toward high HDI outcomes

**Effect:**
- More balanced than GDP-weighted: no single country exceeds 1.5% weight
- Produces a middle-range value ($2.20)
- Does not scale with population (HDI is a 0–1 score, not an extensive quantity)
- Effectively a quality-adjusted version of unweighted averaging

### 2.6 PPP-Adjusted Variants

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

The weighting study (`workbench/studies/weighting/`) computed CHIP under five
aggregation schemes using PWT 11.0 data, averaged over 2018–2022.  Heritage
Foundation freedom scores (2025 edition) and UNDP Human Development Index
values (2022) were merged at the country level.  The methodology and full
data are documented in `workbench/studies/weighting/FINDINGS.md`.

### 4.1 Five Schemes, Five Answers

| Scheme | CHIP ($/hr) | Countries | Top Contributor | Top Weight |
|--------|------------|-----------|-----------------|------------|
| Freedom-weighted (GDP × Heritage) | $2.85 | 79 | USA | 27.1% |
| GDP-weighted (original method) | $2.68 | 85 | USA | 24.0% |
| HDI-weighted (UNDP HDI) | $2.20 | 85 | Switzerland | 1.5% |
| Unweighted (equal per country) | $2.00 | 85 | (equal) | 1.2% |
| Labor-weighted (PWT employment) | $1.67 | 85 | USA | 8.0% |

The spread is $1.17 — from $1.67 (labor) to $2.85 (freedom) — representing
a 51% range around the mean of $2.28.  The coefficient of variation across
the five schemes is 21%.  This is not a rounding error; the weighting
decision is a first-order methodological choice.

### 4.2 Elimination by Reasoning

Not all five schemes are equally defensible.  We can narrow the field by
examining the biases each introduces.

**Freedom-weighted ($2.85) — eliminated.**  Section 3.4 hypothesized that
freedom-weighting would directly operationalize the CHIP definition's "free
market" requirement, producing a value between GDP-weighted and unweighted.
The empirical result was the opposite: freedom-weighting produced the
*highest* value of all five schemes, 6% above GDP-weighted.  This occurred
because the Heritage Foundation index strongly correlates with GDP per
capita, so the GDP × freedom product *amplifies* the rich-country bias
rather than correcting it.  The USA alone accounts for 27% of the weight.
Furthermore, the Heritage index is published by a politically aligned think
tank; its component scores (e.g., "labor freedom") embed editorial judgments
that the paper's reader may not share.  Freedom-weighting is informative as
a data point but should not be adopted as the primary methodology.

**Unweighted ($2.00) — eliminated.**  The unweighted average treats each
country as an independent observation of equal validity.  This is
defensible in laboratory science — each measurement of a physical constant
contributes equally — but inappropriate here because country borders are
arbitrary.  Luxembourg (population 650,000) and India (population 1.4
billion) receive identical weight.  A tiny tax-haven economy and a
continent-scale labor market are not equally informative about the global
price of labor.  Unweighted averaging systematically overrepresents small
countries and is vulnerable to sample composition effects.

**Labor-weighted ($1.67) — eliminated.**  Labor-weighting answers the
question "what does the average worker on Earth earn?" — a legitimate
question, but a different one from what CHIP asks.  CHIP asks: "what
*should* an hour of unskilled labor be worth in a well-functioning market?"
A worker in a country with no capital, broken institutions, and no
functioning labor market is not providing useful signal about that
equilibrium.  Their artificially depressed wage — driven by capital scarcity
and institutional failure, not by the marginal product of their labor —
pulls the estimate below any plausible free-market level.  Additionally,
labor-weighting gives developing-world populations such dominance (India +
China alone account for ~40% of weight) that the result largely reflects
South Asian and Chinese wage conditions, which are among the most distorted
in the sample.

This leaves two serious contenders: **GDP-weighted ($2.68)** and
**HDI-weighted ($2.20)**.

### 4.3 GDP vs HDI: The Final Question

Both GDP-weighting and HDI-weighting give more influence to countries where
markets function relatively well.  But they differ structurally:

**GDP-weighting** says: *"Larger, more productive economies count more
because economic output reflects how much value labor actually creates."*
GDP naturally scales with both population and productivity.  A country with
10x the population and equal per-capita productivity has 10x the weight.
This means GDP-weighting implicitly accounts for population — large
countries with large labor markets have proportionally more influence.

**HDI-weighting** says: *"Countries where people live well — measured by
health, education, and income — are countries where labor markets function
well."*  The UNDP Human Development Index is politically neutral, widely
respected, and captures "standard of living" more directly than GDP alone.

However, HDI-weighting suffers from a version of the same problem that
disqualified unweighted averaging: **country borders are arbitrary, and HDI
does not scale with population.**  HDI is a 0–1 score that applies
uniformly to all citizens of a country.  Norway (5.4 million people,
HDI 0.967) receives almost the same per-citizen weight as India (1.4
billion, HDI 0.644).  The result is that a Norwegian worker has roughly
260× more influence per capita than an Indian worker.  No single country
exceeds 1.5% of the HDI-weighted total — which sounds balanced but actually
means that population is almost completely ignored.  HDI-weighting is
effectively a softer version of unweighted averaging, just with a quality
adjustment.

GDP-weighting avoids this because GDP is an *extensive* quantity — it grows
with population.  This is a genuine structural advantage.  When measuring a
global labor rate, the size of a country's labor market should matter.

**Two additional considerations favor GDP:**

- **Continuity.**  The original study used GDP-weighting.  Changing the
  methodology changes the number.  Unless there is a strong reason to
  switch, consistency with the published historical record reduces
  confusion and strengthens trust.

- **The CHIP definition itself.**  As discussed in Section 3.5, the
  canonical definition emphasizes a "free and balanced market" — language
  that foregrounds economic efficiency, not human welfare.  GDP, as a
  measure of productive output, is more directly aligned with this framing
  than HDI, which measures development outcomes.

**Verdict:** GDP-weighting is the better choice.  It accounts for
population, aligns with the CHIP definition, avoids reliance on subjective
indices, and provides continuity with the original study.

### 4.4 Addressing the Circularity Concern

A natural objection: if GDP-weighting gives 24% of the weight to the USA
and emphasizes wealthy countries, doesn't this make CHIP a self-confirming
measure of rich-country wages?

No — because of the **distortion factor (θ)**.  The CHIP pipeline does not
simply take US wages and aggregate them.  For each country, it computes the
marginal product of labor (from the Cobb-Douglas production function) and
compares it to the observed average wage.  The ratio θ = MPL / average_wage
captures how much a country's labor market deviates from the competitive
equilibrium.  The country's CHIP contribution is then:

$$CHIP_j = \text{elementary\_wage}_j \times \theta_j$$

If a country overpays its workers relative to their marginal product
(θ < 1), its CHIP contribution is *reduced*.  If a country underpays
(θ > 1), its contribution is *increased*.  GDP-weighting determines *how
much the USA matters*, but θ determines *what the USA contributes*.  A
wealthy country with inflated wages and low θ does not drag the global
CHIP upward — the distortion factor corrects for exactly this.

This breaks the circularity.  The production function, not the raw wage,
determines value.

### 4.5 Country Multipliers

Using GDP-weighted CHIP ($2.68/hr) as the reference, each country receives
a **multiplier** indicating how its unskilled labor valuation compares to
the global norm:

| Country | CHIP ($/hr) | Multiplier |
|---------|------------|------------|
| Switzerland | $6.39 | 2.39× |
| Ireland | $5.38 | 2.01× |
| Austria | $5.13 | 1.92× |
| Germany | $4.99 | 1.86× |
| Norway | $4.90 | 1.83× |
| ... | ... | ... |
| **Global (GDP-weighted)** | **$2.68** | **1.00×** |
| ... | ... | ... |
| Uganda | $0.17 | 0.06× |
| Tanzania | $0.15 | 0.06× |
| Mali | $0.15 | 0.05× |
| Pakistan | $0.13 | 0.05× |
| Egypt | $0.10 | 0.04× |

Of 85 countries in the pipeline, 22 have multipliers above 1.0 (workers
paid above the global CHIP) and 63 have multipliers below 1.0.  The median
multiplier is 0.64, confirming that most of the world's labor markets pay
well below the global CHIP.  The full table is available at
`workbench/studies/weighting/output/csv/country_multipliers.csv`.

These multipliers give users in any country an immediate, intuitive sense
of local labor valuation relative to the global norm — directly supporting
Design Goal 10.  They should be published alongside the global CHIP value,
with the caveat that individual-country estimates are more volatile than the
global aggregate (see the stability study: country-level CHIP revisions
across PWT versions can exceed 50%).

---

## 5. Recommendations

### 5.1 Use GDP-Weighted Aggregation

GDP-weighting is the recommended primary methodology.  The empirical
analysis in Section 4 established this through a process of elimination:

1. Freedom-weighting amplifies rich-country bias and depends on a
   politically opinionated index — eliminated.
2. Unweighted averaging ignores population and treats arbitrary borders
   as scientifically meaningful — eliminated.
3. Labor-weighting answers the wrong question ("what do workers earn?"
   rather than "what should labor be worth?") — eliminated.
4. HDI-weighting is balanced but does not scale with population, suffering
   from a softer version of the unweighted problem.
5. GDP-weighting accounts for population, aligns with the CHIP definition's
   emphasis on productive efficiency, provides continuity with the original
   study, and its circularity concern is addressed by the distortion factor.

The GDP-weighted CHIP value using PWT 11.0 data (2018–2022 average) is
**$2.68/hour** (85 countries).

### 5.2 Publish the Full Range for Transparency

While a single value is required for practical use, the methodology
documentation should disclose the full sensitivity range:

| Scheme | CHIP |
|--------|------|
| Freedom-weighted | $2.85 |
| **GDP-weighted (recommended)** | **$2.68** |
| HDI-weighted | $2.20 |
| Unweighted | $2.00 |
| Labor-weighted | $1.67 |

This transparency allows external reviewers to assess whether the GDP
choice is reasonable and builds credibility by demonstrating that the
range has been explored.

### 5.3 Publish Country Multipliers

Per-country multipliers (Section 4.5) should be published alongside the
global CHIP value.  They give users an immediate sense of local labor
valuation and support integration by MyCHIPs nodes operating in specific
jurisdictions.

Multipliers should carry a **PWT version label**, since the stability
study found that individual-country CHIP values can shift by 50%+ across
PWT releases.

### 5.4 Acknowledge the Philosophical Nature of the Choice

The weighting decision is ultimately philosophical, not scientific.  The
data can tell us *what each scheme produces* but not *which is correct*.
The paper should be explicit that GDP-weighting encodes a prior — that
productive economic output is the best available proxy for a hypothetical
free-market equilibrium — and that reasonable people could prefer
HDI-weighting as a second-best alternative.

The unknowable ground truth is what wages would be in a truly free, global
labor market with no borders or barriers.  GDP-weighted CHIP ($2.68) and
HDI-weighted CHIP ($2.20) likely bracket that value from above and below.
The true equilibrium is somewhere in that $0.48 range — a much tighter
bound than the full $1.17 spread across all five schemes.

---

## 6. References

Bateman, K. (2022). *Got Choices*. https://gotchoices.org

Heritage Foundation. (2025). *2025 Index of Economic Freedom*.
https://www.heritage.org/index/

International Labour Organization. ILOSTAT Database. https://ilostat.ilo.org

Feenstra, R.C., Inklaar, R., & Timmer, M.P. (2015). The Next Generation
of the Penn World Table. *American Economic Review*, 105(10): 3150-3182.

United Nations Development Programme. (2025). *Human Development Report
2024/2025*. https://hdr.undp.org

---

*Document status: COMPLETE — updated 2026-02-09 with empirical results from
the weighting study (PWT 11.0, Heritage 2025, HDI 2022).*
