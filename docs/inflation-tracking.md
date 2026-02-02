# CHIP Value and Currency Inflation: A Predictive Analysis

**Abstract**

This paper examines whether the CHIP valuation methodology should track currency inflation over time. We analyze the original study's use of a GDP deflator, argue that this approach—while appropriate for academic time-series analysis—conflicts with the practical needs of MyCHIPs users, and propose alternative methodologies better suited to producing actionable, current-year CHIP estimates. Preliminary empirical evidence reveals significant sensitivity to country composition and time-window selection. We conclude with testable hypotheses for future empirical validation.

---

## 1. Introduction

### 1.1 The Core Question

The CHIP (Credit Hour In Pool) is a proposed currency anchored to the value of human labor. A natural question arises: if world currencies inflate over time, should we expect the CHIP value—expressed in US dollars—to increase, decrease, or remain stable?

This question is not merely academic. The answer has direct implications for how MyCHIPs software should present CHIP values to users and whether the current estimation methodology serves its intended practical purpose.

### 1.2 Why This Matters

The CHIP estimate serves a specific function: helping users understand the value of CHIP-denominated pledges (IOUs) in the MyCHIPs system. When a user receives a pledge for "10 CHIPs," they need to know what that pledge is worth in their native currency. The estimator exists to help answer this question.

If CHIP naturally tracks inflation—rising as currencies lose purchasing power—then CHIP serves as a built-in hedge against currency devaluation. If CHIP is expressed in constant (deflated) dollars, users must perform additional calculations to understand current value, introducing complexity and potential for error.

### 1.3 Scope of This Analysis

This paper proceeds as follows: Section 2 establishes the philosophical foundation for using labor as a value index. Section 3 examines the original study's methodology, including its use of a GDP deflator. Section 4 identifies the mismatch between academic and practical goals. Section 5 describes expected behavior without deflation. Section 6 proposes alternative methodological approaches. Section 7 offers recommendations. Section 8 presents preliminary empirical evidence and testable hypotheses. Section 9 concludes.

---

## 2. Philosophical Foundation: Labor as the Universal Index

### 2.1 The Problem with Fiat Currency

All fiat currencies are subject to inflation, manipulation, and instability. Central banks expand money supplies, governments accumulate debt, and purchasing power erodes over time. This creates a fundamental problem for any system that seeks to store or transfer value across time: the unit of measurement itself is unstable.

More deeply, there is no "natural unit" for measuring value. Every value is expressed as a multiple of some other value—dollars per hour, ounces per dollar, hours per loaf of bread. Value is inherently relational.

### 2.2 Alternative Approaches to Stable Value

Various approaches have been proposed to create stable value indices:

**Basket of goods**: Some alternative currencies and inflation indices use a fixed basket of commodities (food, housing, energy) to track purchasing power. This approach is intuitive but requires ongoing decisions about basket composition as consumption patterns change.

**Gold standard**: Precious metals have served as value anchors for millennia. Gold is durable, divisible, and scarce. However, gold supply is subject to mining discoveries and central bank manipulation, and its value fluctuates based on industrial demand and speculative activity.

### 2.3 The CHIP Theory: Labor as the Index of All Value

The CHIP approach takes a different path, positing that **nominal unskilled labor** constitutes the ultimate index of all goods and services. This rests on several observations:

First, all goods and services are ultimately produced by labor. Capital equipment, raw materials, and land all require human effort to extract, process, and transform into useful outputs. Labor is the fundamental input to all economic activity.

Second, labor is universal. Every adult human being possesses their own supply of labor hours. Unlike gold or land, labor cannot be monopolized by a small group of holders.

Third, labor is resistant to manipulation. While wages can be suppressed through policy or market power, the underlying reality of human productive capacity is difficult to distort at a global scale.

Fourth, the labor supply naturally scales with population, growing organically with the economy rather than being subject to arbitrary expansion like fiat currency.

### 2.4 The CHIP Definition

The formal CHIP definition specifies:

> One CHIP = the value of one continuously applied hour of adult human work, in circumstances where there is neither shortage nor surplus of willing labor, where the job requires only minimal training, and without considering productivity gains from capital equipment.

The key word is **nominal**—not adjusted for inflation. A CHIP represents what one hour of baseline labor is worth at current market prices, not what it was worth in some historical base year.

---

## 3. The Original Study's Methodology

### 3.1 Core Calculation

The original CHIP valuation study employed a Solow-Swan growth model with Cobb-Douglas production function to estimate the value of unskilled labor. The core calculation can be expressed as:

```
CHIP = Elementary_Wage × Distortion_Factor
```

Where the distortion factor θ = MPL / Actual_Wage represents the ratio between the marginal product of labor (what labor "should" earn in a frictionless market) and actual observed wages. The elementary wage comes from ILOSTAT data for ISCO "Elementary Occupations"—the closest empirical proxy for unskilled labor.

### 3.2 Key Methodological Features

The study incorporated several important methodological choices:

**Deflation to base year**: All wages were deflated using the US GDP deflator to constant 2017 dollars. This converted nominal wages from different years into comparable real values.

**GDP-weighted aggregation**: Country-level CHIP estimates were aggregated to a global value using GDP weights. This gives greater influence to larger, more productive economies—argued to better approximate a frictionless global market.

**Cross-year pooling**: Data from approximately 1992 to 2019 were pooled together, with the final estimate representing an average across this entire period.

### 3.3 How the Deflator Works

The GDP deflator converts nominal values to real (constant-dollar) values using the formula:

```
Real Wage (2017$) = Nominal Wage × (Deflator_2017 / Deflator_year)
```

For example, a $10 nominal wage in 2005 becomes approximately $11.76 in 2017 dollars (adjusting for the ~18% inflation between 2005 and 2017). Similarly, a $15 nominal wage in 2019 becomes approximately $13.89 in 2017 dollars (adjusting downward for the ~8% inflation since 2017).

After deflation, wages from different years can be meaningfully compared and averaged.

### 3.4 Why an Economist Would Deflate

The use of deflation is standard practice in academic economics when analyzing time-series data. The original study pooled data from multiple years to increase statistical power and country coverage. From an econometric standpoint, this pooling requires deflation:

Without deflation, one cannot meaningfully average $10 (2005 dollars) with $15 (2019 dollars)—they represent different units. Fixed-effects regression requires comparable observations across time. Deflation provides that comparability.

For academic purposes—producing a rigorous, peer-reviewable analysis of labor value across time—deflation was the correct methodological choice.

### 3.5 Interpreting the Result

The original study produced an estimate of approximately $2.53 per hour (our Python reproduction yields $2.56). This figure represents **the value of one CHIP in 2017 dollars**.

To convert this to current nominal dollars, one would multiply by the cumulative inflation since 2017:

```
Nominal CHIP (2026) ≈ $2.56 × (Deflator_2026 / Deflator_2017)
```

If cumulative inflation since 2017 has been approximately 25%, this suggests a current nominal CHIP value of roughly $3.20.

---

## 4. The Mismatch: Academic vs. Practical Goals

### 4.1 What the Study Answers

The original study effectively answers the question: "What is the average real value of one hour of unskilled labor, measured in 2017 dollars, across the period 1992-2019?"

This is a valid and interesting academic question. It provides a stable, comparable metric for analyzing labor value trends over time.

### 4.2 What MyCHIPs Needs

The MyCHIPs system requires an answer to a different question: "What is one CHIP worth in dollars **right now**?"

When a user opens their MyCHIPs wallet and sees a balance of 100 CHIPs, they need to understand immediately what that means in their native currency. They should not need to look up deflator indices or perform arithmetic.

### 4.3 The Fundamental Mismatch

These two questions—the academic and the practical—have fundamentally different requirements:

| Academic Goal | Practical Goal |
|---------------|----------------|
| Compare values across time periods | Know today's price |
| Pool data for statistical power | Use current market conditions |
| Produce "timeless" real estimate | Produce actionable nominal value |
| Support peer review and publication | Support wallet user interface |

The original study optimized for the left column. MyCHIPs requires optimization for the right column.

### 4.4 The User Experience Problem

Consider the user experience when CHIP is expressed in 2017 dollars:

1. User receives pledge for "10 CHIPs"
2. User looks up CHIP value: "$2.56"
3. User thinks: "So that's $25.60"
4. **Wrong**—that's $25.60 in 2017 dollars
5. User must find current deflator index
6. User must multiply: $25.60 × 1.25 ≈ $32.00 in 2026 dollars

This complexity undermines the CHIP's purpose as an intuitive, stable value anchor.

### 4.5 The Deflator as Contextual Error

To be clear: the original study did not make an error in using deflation. For its academic purposes, deflation was correct. The error arises only when applying this academic methodology to a practical use case with different requirements.

The CHIP definition specifies **nominal** unskilled labor. If labor costs $3/hour today, CHIP equals $3. If labor costs $4/hour next year, CHIP equals $4. The deflator removes precisely this feature—the natural tracking of nominal labor costs—that makes CHIP useful as a practical value index.

---

## 5. Expected Behavior Without Deflation

### 5.1 Natural Inflation Tracking

If we remove deflation from the CHIP methodology, we would expect the following behavior:

CHIP values should **increase** as currencies inflate, tracking the rising nominal cost of labor. CHIP would serve as a natural hedge against currency devaluation. One CHIP would always equal "one hour of unskilled labor at current prices."

This is arguably not a bug to be corrected but a core feature of the labor-based value anchor.

### 5.2 Real Economic Changes

Even in nominal terms, CHIP could change due to real economic factors beyond inflation:

**Productivity gains**: If workers become more productive (due to technology, education, or capital deepening), the marginal product of labor increases, potentially raising the distortion-adjusted CHIP value.

**Globalization**: Integration of low-wage countries into global markets could shift the GDP-weighted average.

**Automation**: Reduced demand for unskilled labor could compress wages at the low end. (See [The Future of Labor Value](labor-value-future.md) for extended analysis of how AI and automation may affect CHIP's long-term viability.)

**Educational shifts**: Changes in workforce composition affect the supply of "unskilled" labor.

### 5.3 The CHIP Philosophy on Real Changes

The CHIP theory accepts that labor value drifts relative to other commodities. This is expected and acceptable. Every commodity value drifts relative to every other—gold versus oil, wheat versus housing, labor versus capital. There is no absolute, unchanging unit of value.

The claim is not that CHIP is perfectly stable, but that it is **more stable and more meaningful** than fiat currency as a value anchor. An hour of human labor represents something real and universal, unlike an arbitrary central bank decree.

### 5.4 Distinguishing Signal from Noise

When analyzing CHIP value changes, we can distinguish between acceptable and problematic sources of variation:

| Change Type | Cause | Acceptable? |
|-------------|-------|-------------|
| Nominal increase | Currency inflation | Yes (expected feature) |
| Real change | Economic fundamentals | Yes (reflects reality) |
| Composition shift | Different countries in sample | No (methodological artifact) |

The third category—composition effects—represents noise that should be minimized through careful methodology.

### 5.5 The Epistemology of Value: Can We Know If Labor Value "Really" Changes?

A deeper question arises: If CHIP value changes over time (in real terms), how do we know whether labor has become more or less valuable in some "absolute" sense, versus our measuring stick (currency, goods basket) changing its value?

**The uncomfortable answer: We probably cannot know with certainty.**

All value is relational. When we say "labor is worth $10/hour," we mean labor trades for a certain quantity of currency. When we say "labor buys 2 loaves of bread," we express labor's value relative to bread. There is no external vantage point from which to observe "absolute" value—if such a thing even exists.

Consider these scenarios:

| Observation | Possible Interpretation A | Possible Interpretation B |
|-------------|---------------------------|---------------------------|
| Labor buys fewer goods | Labor became less valuable | Goods became more valuable |
| Labor trades for more currency | Labor became more valuable | Currency inflated |
| Labor buys fewer goods AND trades for more currency | Currency inflated faster than labor-goods exchange changed | Complex combination |

We can partially distinguish between interpretations by comparing labor to multiple reference points (currency, goods basket, capital, other commodities). If labor's value drops relative to *everything else*, that suggests labor itself is losing value. But this comparison is never perfect—every reference point has its own dynamics.

**The AI and automation question** makes this concrete: As artificial intelligence and robotics advance, will demand for unskilled human labor decline? If so, the "real" value of unskilled labor—relative to goods, capital, and skilled labor—may fall. CHIP would decline in real terms.

**The pragmatic resolution**: CHIP does not claim to be an immutable, absolute standard. It claims to be:

1. **More stable** than fiat currency (which can be inflated at will)
2. **More meaningful** than arbitrary monetary units (rooted in human productive capacity)
3. **Honest** about economic reality (if labor value truly declines, CHIP reflects that)

If automation reduces global demand for unskilled labor, CHIP declining is not a failure of the methodology—it is the methodology working correctly. CHIP measures what an hour of baseline human labor is worth in the actual economy, not in some idealized abstraction.

We accept this uncertainty as inherent to any value measurement. By anchoring to labor, we choose a reference point that is universal, manipulation-resistant, and meaningful—while acknowledging that even this anchor drifts relative to other values over time.

---

## 6. Alternative Methodological Approaches

### 6.1 Simple Approach: Most Recent Year Only

The simplest alternative is to abandon cross-year pooling entirely:

1. Use only the most recent year with complete data (e.g., 2024)
2. No deflation needed—data from a single year is already in that year's dollars
3. Update the estimate periodically with fresh data

This approach directly answers "what is CHIP worth today?" with minimal complexity.

**Advantages**: Simple to implement and explain. No deflation confusion. Directly actionable for users.

**Disadvantages**: Higher volatility. Dependent on single year's data quality. Some countries may lack data in the most recent year.

### 6.2 Windowed Average: Centered Window

A more sophisticated approach uses adjacent years, inflation-adjusted to a target year:

```
CHIP(2019) = Average of:
  - 2018 data × (Deflator_2019 / Deflator_2018)
  - 2019 data × 1.0
  - 2020 data × (Deflator_2019 / Deflator_2020)
```

All values are expressed in 2019 dollars. The result is a smoothed estimate for 2019.

**Key insight**: Deflation is used for comparability **within the window**, but the result is expressed in **target year nominal dollars**—not a fixed historical base year. Each year's estimate is in that year's own dollars.

**Advantages**: Smooths year-to-year volatility. Uses deflation appropriately for within-window comparability. Produces nominal values for each target year.

**Disadvantages**: Requires waiting for future data (2020 values not available until after 2020).

### 6.3 Windowed Average: Trailing Window

To avoid forward-looking data requirements, use only past data:

```
CHIP(2019) = Average of:
  - 2017 data × (Deflator_2019 / Deflator_2017)
  - 2018 data × (Deflator_2019 / Deflator_2018)
  - 2019 data × 1.0
```

**Advantages**: Available immediately after each year closes. Conservative (uses only realized data). Still produces nominal current-year values.

**Disadvantages**: Introduces lag. May not reflect very recent economic changes.

### 6.4 Sliding Time Series

Applying the trailing window to each year produces a time series of nominal CHIP values:

| Year | Window Used | CHIP Value |
|------|-------------|------------|
| 2017 | 2015-2017 | $2.30 (2017$) |
| 2018 | 2016-2018 | $2.45 (2018$) |
| 2019 | 2017-2019 | $2.60 (2019$) |
| 2020 | 2018-2020 | $2.75 (2020$) |

*Note: Values are illustrative.*

This produces a nominal time series that should trend upward with inflation—the expected behavior for a labor-based value index.

### 6.5 Comparison of Approaches

| Approach | Volatility | Lag | Complexity | Result Units |
|----------|------------|-----|------------|--------------|
| Single year | High | None | Low | Nominal (current) |
| Centered window | Low | Some | Medium | Nominal (target year) |
| Trailing window | Low | More | Medium | Nominal (target year) |
| Original (pooled, deflated) | Very low | High | Medium | Real (base year) |

The original approach minimizes volatility but produces results in units that require conversion for practical use.

---

## 7. Recommendations

### 7.1 For the CHIP Estimator (MyCHIPs Use)

Based on this analysis, we recommend the following for production CHIP estimates:

1. **Remove fixed-base deflation** from the core calculation
2. Express CHIP in **nominal current-year dollars**
3. Use a **trailing windowed average** (3-5 years) for stability
4. Report the **year** of the estimate clearly (e.g., "CHIP 2024: $3.15")
5. Update **annually** with fresh data

### 7.2 For Academic Analysis

For scholarly work requiring time-series comparability:

1. Continue to provide deflated (real) values as supplementary information
2. Hold country sample constant when making temporal comparisons
3. Report both nominal and real values for transparency
4. Clearly label units (e.g., "2017 USD" vs. "current USD")

### 7.3 For MyCHIPs Implementation

For the user-facing software:

1. Publish CHIP value with clear date stamp
2. Update periodically (annually) with fresh data
3. Communicate that CHIP tracks labor costs, which includes inflation
4. Optionally display trend information: "CHIP 2024: $3.15 (up 3% from 2023)"

---

## 8. Preliminary Empirical Evidence

### 8.1 Test Methodology

Using the Python reproduction pipeline with `data_source: "original"`, we calculated CHIP values for different time windows. All values were deflated to 2017 dollars per the original methodology, allowing us to observe how the methodology behaves across different periods.

### 8.2 Results

| Period | CHIP Value (2017$) | Countries in Sample |
|--------|-------------------|---------------------|
| **1992-2019 (baseline)** | **$2.56** | **90** |
| 2006-2008 | $0.98 | 27 |
| 2010-2012 | $1.42 | 38 |
| 2014-2016 | $1.91 | 57 |
| 2017-2019 | $1.74 | 62 |

The baseline ($2.56) matches the reproduction of the original study. It uses all available data from 1992-2019, resulting in more countries and extensive cross-year averaging.

### 8.3 Observations

**Rising trend in deflated terms**: CHIP nearly doubled from $0.98 (2006-08) to $1.91 (2014-16), even after deflation. However, this does NOT necessarily mean real wages rose globally.

**Composition effect dominates**: The country count expanded dramatically from 27 to 62 over the test periods. The observed rise and subsequent fall likely reflects **which countries are in the sample** rather than underlying wage trends. Early periods include only countries with complete data—likely wealthier nations with better statistical infrastructure. Later periods add more countries as ILOSTAT coverage expands, potentially including both higher-wage countries (improving their reporting) and lower-wage developing nations.

**The deflator worked correctly**: If inflation were the primary driver, deflated values would be stable across periods. The observed volatility confirms that deflation is successfully removing price-level effects. What remains is a combination of composition effects and real economic changes.

**Key insight**: To isolate real wage trends from composition effects, future analysis must hold the country sample constant across all periods.

**Aggregation sensitivity**: The full-range CHIP ($2.56) is significantly higher than the arithmetic average of individual periods (~$1.51). This reveals that the methodology is highly sensitive to window selection and data completeness. High-wage countries may contribute data in years not covered by narrow windows, and the Cobb-Douglas estimation behaves differently with varying amounts of pooled data.

### 8.4 Implications

These findings suggest that the current methodology, while academically rigorous, produces results that are difficult to interpret for practical purposes:

1. The deflator masks the expected inflation-tracking behavior
2. Country composition is a major confounding factor
3. Window selection dramatically affects results
4. Cross-year pooling obscures temporal trends

### 8.5 Testable Hypotheses

Based on this analysis, we propose the following hypotheses for empirical testing in subsequent modeling work:

**H1: Nominal CHIP tracks inflation**

If we calculate CHIP without deflation (nominal terms), the value should increase over time, roughly tracking CPI or GDP deflator indices. A rising nominal CHIP would validate that the methodology captures the declining purchasing power of fiat currency.

**H2: Deflated CHIP is stable when composition is controlled**

If we hold the country sample constant across all periods (using only countries with complete data throughout), deflated CHIP values should be relatively stable. Observed stability would confirm that the volatility in our preliminary results stems from composition effects rather than real economic changes.

**H3: Windowed averaging produces coherent time series**

A trailing-window methodology (e.g., 3-year rolling average, inflation-adjusted to each target year) should produce a smooth, interpretable time series of nominal CHIP values. This time series should trend upward over time, consistent with cumulative inflation.

**H4: Recent-year CHIP is more actionable for MyCHIPs**

A nominal CHIP calculated from recent data (e.g., 2022-2024) will provide a more useful, immediately interpretable value for MyCHIPs users than the current deflated, all-years-pooled approach.

### 8.6 Next Steps for Validation

Testing these hypotheses requires building a new estimation pipeline in the `estimates/` project:

1. Implement trailing window methodology with inflation adjustment to target year
2. Create option to run without fixed-base deflation (nominal output)
3. Develop country-filter capability to hold sample constant
4. Compare nominal CHIP trend to official inflation benchmarks
5. Produce sliding time series from earliest available year to present

---

## 9. Conclusions

### 9.1 Summary of Findings

This analysis has established several key points:

First, **the original study's use of deflation was appropriate for its academic purposes**. Cross-year pooling requires comparable units, and deflation provides that comparability. The methodology is sound for producing a peer-reviewable analysis of global labor value.

Second, **deflation conflicts with the practical MyCHIPs use case**. Users need to know what CHIP is worth today, in today's dollars. Expressing CHIP in 2017 dollars requires users to perform inflation adjustments, undermining the simplicity that makes CHIP valuable as a practical currency anchor.

Third, **CHIP should track inflation** when expressed in nominal terms. This is a feature, not a bug. A labor-based value index naturally rises with the nominal cost of labor. This provides users with a stable value reference that automatically adjusts for currency devaluation.

Fourth, **windowed approaches** can provide stability while maintaining current-year relevance. By using a trailing 3-5 year window with inflation adjustment to the target year, we can smooth year-to-year volatility while still producing nominal values for each year.

Fifth, **CHIP does not claim absolute stability**. If real economic changes (such as automation reducing demand for unskilled labor) cause labor value to decline relative to goods and capital, CHIP should reflect that decline. The distinction between inflation and real-value-change is partially observable but ultimately uncertain. CHIP is chosen as an anchor because labor is universal and meaningful, not because it is immutable.

### 9.2 The Path Forward

This analysis motivates the creation of a new `estimates/` project to implement and test the recommended methodology:

1. Build a pipeline that produces nominal, current-year CHIP estimates
2. Implement trailing window averaging with inflation adjustment
3. Test the hypotheses established in Section 8.5
4. Compare results to official inflation benchmarks
5. Produce a validated time series of historical CHIP values
6. Establish a process for annual updates

### 9.3 The CHIP Value Proposition

By anchoring to labor rather than a basket of goods or precious metals, CHIP offers unique advantages as a value index:

**Stability without rigidity**: CHIP tracks the real, evolving value of human productive capacity rather than being fixed to an arbitrary historical level.

**Natural inflation tracking**: Nominal CHIP rises with labor costs, automatically adjusting for currency devaluation without requiring explicit inflation calculations.

**Universal accessibility**: Everyone possesses their own supply of labor hours, making the CHIP standard intuitively meaningful across all cultures and economic systems.

The work ahead is to implement a methodology that fully realizes these advantages for practical use.

---

## References

- Bateman, K. (2022). *Got Choices*. https://gotchoices.org
- CHIP Definition. https://gotchoices.org/mychips/definition.html
- Feenstra, R.C., Inklaar, R., & Timmer, M.P. (2015). Penn World Table 10.0
- FRED Economic Data. US GDP Deflator (USAGDPDEFAISMEI)
- International Labour Organization. ILOSTAT Database. https://ilostat.ilo.org
- Solow, R.M. (1956). "A Contribution to the Theory of Economic Growth." *Quarterly Journal of Economics*, 70(1), 65-94.
