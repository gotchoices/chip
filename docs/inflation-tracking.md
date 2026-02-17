# CHIP Value and Currency Inflation: A Predictive Analysis

**Abstract**

This paper examines whether the CHIP valuation methodology should track currency inflation over time. We analyze the original study's use of a GDP deflator, argue that this approach—while appropriate for academic time-series analysis—conflicts with the practical needs of MyCHIPs users, and propose alternative methodologies better suited to producing actionable, current-year CHIP estimates. We develop the concept of a "deflationary baseline"—the expectation that, in a free economy, technology should make goods cheaper over time—and examine what prices should do when denominated in CHIPs. Empirical results from workbench studies confirm that real CHIP is approximately stable, that nominal CHIP tracks inflation, and that a 5-year trailing window produces a smooth, defensible series.

---

## 1. Introduction

### 1.1 The Core Question

The CHIP (Credit Hour In Pool) is a proposed currency anchored to the value of human labor. A natural question arises: if world currencies inflate over time, should we expect the CHIP value—expressed in US dollars—to increase, decrease, or remain stable?

This question is not merely academic. The answer has direct implications for how MyCHIPs software should present CHIP values to users and whether the current estimation methodology serves its intended practical purpose.

### 1.2 Why This Matters

The CHIP estimate serves a specific function: helping users understand the value of CHIP-denominated pledges (IOUs) in the MyCHIPs system. When a user receives a pledge for "10 CHIPs," they need to know what that pledge is worth in their native currency. The estimator exists to help answer this question.

If CHIP naturally tracks inflation—rising as currencies lose purchasing power—then CHIP serves as a built-in hedge against currency devaluation. If CHIP is expressed in constant (deflated) dollars, users must perform additional calculations to understand current value, introducing complexity and potential for error.

### 1.3 Scope of This Analysis

This paper proceeds as follows: Section 2 establishes the philosophical foundation for using labor as a value index. Section 3 examines the original study's methodology, including its use of a GDP deflator. Section 4 identifies the mismatch between academic and practical goals. Section 5 describes expected behavior without deflation, including the natural deflationary baseline, Baumol's cost disease, and what prices should do when denominated in CHIPs. Section 6 proposes alternative methodological approaches. Section 7 offers recommendations for production use, implementation, and market dynamics around recalculations. Section 8 presents empirical evidence from the workbench studies. Section 9 concludes.

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

The original study produced an estimate of approximately $2.53 per hour using frozen CSV data (our Python reproduction yields $2.56 from the same data, or $2.35 with fresh API data). This figure represents **the value of one CHIP in 2017 dollars**.

To convert this to current nominal dollars, one would multiply by the cumulative inflation since 2017:

```
Nominal CHIP (2026) ≈ $2.53 × (Deflator_2026 / Deflator_2017)
```

With cumulative US inflation of approximately 26% since 2017, this gives a nominal value of roughly $3.18—which is, in fact, what chipcentral.net currently displays. The workbench production study (using PWT 11.0 and fresh data) independently calculates the 2022 nominal CHIP at $3.17, confirming that the original CPI extrapolation has tracked reality remarkably well over 5 years of compounding.

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

### 5.2 The Deflationary Baseline

We have grown so accustomed to rising prices that inflation feels like the natural order. But it is not. In a free economy with improving technology, the natural trajectory of prices is **downward**.

Consider: a bushel of corn required dozens of man-hours to produce in 1800. Today, it requires minutes of tractor time. The real resource cost of corn has plummeted. The same is true of clothing, steel, lighting, computation, communication, and nearly every manufactured good. Technology relentlessly reduces the human effort required to produce things.

Computers obeyed this deflationary trajectory visibly for decades. A megabyte of storage cost thousands of dollars in the 1980s and is effectively free today. This is the natural direction: as processes improve, outputs get cheaper.

Pre-Federal Reserve America experienced long periods of gentle deflation. From 1870 to 1900, the US price level fell roughly 40% while real GDP more than doubled. Prices fell because productivity increased faster than the money supply grew. People's wages bought more each year. This was prosperity, not crisis.

**Monetary expansion masks this natural deflation.** Since the founding of the Federal Reserve in 1913, the US dollar has lost over 96% of its purchasing power. Central banks expand the money supply faster than productivity grows, turning what should be gently falling prices into relentlessly rising ones. The rising price of a bushel of corn—from $0.50 to $5.00 over a century—does not reflect corn getting harder to produce. It reflects the dollar becoming worth less.

This matters for CHIP because it reframes the question. When we see nominal CHIP rising over time, we should not think "labor is getting more expensive." We should think "the currency is getting weaker, and CHIP is faithfully reporting that." The real cost of an hour of unskilled labor, measured in goods and services, may actually be falling—or at least holding steady—even as nominal CHIP climbs.

### 5.3 Real Economic Forces That Can Change CHIP

Even in nominal terms, CHIP could change due to real economic factors beyond monetary inflation:

**Productivity gains**: If workers become more productive (due to technology, education, or capital deepening), the marginal product of labor increases, potentially raising the distortion-adjusted CHIP value.

**Globalization**: Integration of low-wage countries into global markets could shift the GDP-weighted average.

**Automation**: Reduced demand for unskilled labor could compress wages at the low end. (See [The Future of Labor Value](labor-value-future.md) for extended analysis of how AI and automation may affect CHIP's long-term viability.)

**Educational shifts**: Changes in workforce composition affect the supply of "unskilled" labor.

**Baumol's cost disease**: Some categories of goods and services systematically resist the deflationary baseline described in Section 5.2. Economist William Baumol observed that labor-intensive services—healthcare, education, legal services, live performance, construction—do not benefit from the same productivity improvements as manufacturing and agriculture. A surgeon's operation takes about as long today as it did in 1950. A teacher still teaches one classroom at a time. These sectors must compete for workers whose *alternative* wages have risen (because manufacturing and technology pay more), so their prices rise in real terms even when the broader economy becomes more efficient. This is not inflation; it is a genuine shift in relative prices, driven by uneven productivity growth.

**Artificial scarcity**: Tariffs, zoning laws, licensing requirements, patent monopolies, and regulatory barriers make specific goods more expensive than they would be in a free market. These are the "distortions" that the CHIP definition explicitly envisions stripping away. A house in a heavily zoned city costs more not because housing is harder to build, but because the right to build is artificially restricted. In the CHIP's hypothetical "worldwide, free, and balanced market," these distortions would not exist.

### 5.4 What Should Prices Do When Denominated in CHIPs?

This is perhaps the most illuminating way to think about CHIP as a unit of account. By measuring prices in CHIPs—hours of unskilled labor—we strip out monetary inflation entirely and expose the underlying real dynamics.

**Most manufactured goods should get cheaper in CHIP terms.** Technology reduces the labor required to produce a television, a shirt, a car. If a TV cost 200 CHIPs in 2005 but only 30 CHIPs today, that reflects genuine progress: less human effort is needed to produce the same output. This is the deflationary baseline made visible.

**Labor-intensive services should stay roughly flat in CHIP terms.** A haircut, a plumbing repair, or an hour of childcare are fundamentally priced in labor already. One hour of a plumber's time costs some multiple of one CHIP, and that multiple reflects the skill premium. Baumol's cost disease means these prices resist deflation, but they also resist inflation—because the numerator (service cost) and the denominator (unskilled labor cost) both move with the labor market.

**Artificially scarce goods may rise in CHIP terms.** If housing zoning restricts supply while demand grows, the CHIP price of a house rises—and this is CHIP working correctly as a measurement tool. The rising CHIP price reveals a real distortion, not a flaw in the index. Similarly, a patented drug may cost thousands of CHIPs precisely because the patent creates artificial scarcity. CHIP makes these distortions visible.

**Commodities present a mixed picture.** Some commodities have genuine supply constraints (finite oil reserves, arable land). Others, like corn, have seen dramatic cost reductions from technology. The CHIP price of each commodity tells an honest story about whether human effort to produce it is rising or falling—unclouded by monetary noise.

This framework resolves the apparent paradox that "everything seems to get more expensive." In dollar terms, yes—because the dollar is losing value. In CHIP terms, most things are getting *cheaper*, some things are holding steady, and the things that are genuinely getting more expensive reveal real constraints or real distortions that merit attention.

### 5.5 The CHIP Philosophy on Real Changes

The CHIP theory accepts that labor value drifts relative to other commodities. This is expected and acceptable. Every commodity value drifts relative to every other—gold versus oil, wheat versus housing, labor versus capital. There is no absolute, unchanging unit of value.

The claim is not that CHIP is perfectly stable, but that it is **more stable and more meaningful** than fiat currency as a value anchor. An hour of human labor represents something real and universal, unlike an arbitrary central bank decree.

Our empirical studies support this claim: real (constant-dollar) CHIP has been approximately stable at $2.80–$3.15/hr from 2005 through 2022 (see Section 8). This suggests the upward pressure on labor value (rising standards of living, increasing opportunity cost of work) and the downward pressure (automation, globalization) have been roughly in balance over this period.

### 5.6 Distinguishing Signal from Noise

When analyzing CHIP value changes, we can distinguish between acceptable and problematic sources of variation:

| Change Type | Cause | Acceptable? |
|-------------|-------|-------------|
| Nominal increase | Currency inflation | Yes (expected feature) |
| Real change | Economic fundamentals | Yes (reflects reality) |
| Composition shift | Different countries in sample | No (methodological artifact) |

The third category—composition effects—represents noise that should be minimized through careful methodology (see Section 8.2 for empirical evidence of this effect and the use of stable panels to control for it).

### 5.7 The Epistemology of Value: Can We Know If Labor Value "Really" Changes?

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

For the user-facing software and infrastructure:

1. Publish CHIP value with clear date stamp
2. Operate a **two-tier update model**:
   - A lightweight **daily/weekly script** extrapolates the latest official base
     value using CPI (or GDP deflator), keeping the published figure current
     without waiting for source data.
   - An **annual recalculation** (or whenever new ILOSTAT/PWT data drops)
     re-runs the full pipeline, updates the base parameters, and "snaps" the
     published value to the more accurate estimate.
3. Communicate that CHIP tracks labor costs, which includes inflation
4. Publish **country-specific multipliers** alongside the global CHIP so users
   can see how their country's labor valuation compares to the global norm
5. Expose global CHIP and country multipliers via a queryable **API endpoint**
6. Optionally display trend information: "CHIP 2024: $3.15 (up 3% from 2023)"

### 7.4 Market Dynamics Around Recalculations

The two-tier update model (Section 7.3) implies periodic "snaps" when the
recalculated base value replaces the CPI-extrapolated estimate.  The
production study (Section 8.5) shows these corrections are typically in the
±5–10% range.  A natural question arises: can market participants game
the snap?

**The CHIP index is an estimate, not a price.**  The published CHIP value is
a reference point — a best-effort estimate of the global cost of one hour of
unskilled labor.  It is not a binding exchange rate, a peg, or a settlement
obligation.  Individual buyers and sellers of CHIPs (or dollars) always set
their own rate based on their own judgment and natural market forces.  The
index is a guideline that helps participants calibrate, not a price they are
compelled to accept.

**Anticipated adjustments should be priced in.**  If market participants
broadly expect the next recalculation to revise CHIP upward (e.g., because
CPI is known to understate inflation), rational actors will begin adjusting
their asking prices in advance.  The "market CHIP" drifts toward the expected
post-snap value before the official number catches up.  On recalculation day,
the published rate simply ratifies what the market had already discovered.
This is the same dynamic that governs exchange rates around anticipated
central bank actions: the announcement becomes a non-event because the
information was already reflected in prices.

**Practical arbitrage is difficult.**  Classical arbitrage requires liquid
markets with low transaction costs.  MyCHIPs is a *credit network* —
positions are trust relationships, not anonymous spot trades.  To "go long"
CHIPs you need willing counterparties, and the friction of establishing and
settling credit lines vastly exceeds the few-percent gain from a predictable
snap.  Combined with the small correction magnitude and the uncertainty in
its direction (COVID years produced both positive and negative surprises),
the theoretical arbitrage opportunity is negligible in practice.

**Design implications.**  Even though gaming risk is low, several design
choices further reduce it:

1. **Recalculate on data availability, not on a calendar date.**  New
   ILOSTAT or PWT releases arrive at irregular times (typically mid-year).
   Processing and publishing the correction promptly eliminates any
   fixed-date anticipation effect.
2. **Publish correction estimates continuously.**  If the daily extrapolation
   script can estimate the likely snap magnitude (e.g., by watching
   preliminary data releases), publishing that estimate removes the
   information asymmetry that arbitrage requires.
3. **Phase in corrections gradually.**  Transitioning the base value
   linearly over 30 days rather than as a step function reduces the
   incentive to time transactions around the cutover.
4. **Keep corrections small.**  More frequent recalculations (quarterly when
   data permits) mechanically reduce snap magnitude, making any remaining
   gaming opportunity even less significant.

The overarching principle is that **the CHIP index follows economic reality;
it does not create it.**  When the index moves, it is because the underlying
data moved.  Participants who adjust their expectations ahead of the official
number are not exploiting the system — they are contributing to efficient
price discovery.

---

## 8. Empirical Evidence

The workbench studies (baseline, timeseries, and production) have now tested the core claims of this paper. This section summarizes the key findings. For detailed methodology and data, see each study's FINDINGS.md.

### 8.1 Deflation Cancels in the CHIP Formula

The most important empirical discovery was mathematical: deflation has **no effect** on the calculated CHIP value. Because CHIP = elementary_wage × (MPL / average_wage), and both wages are scaled by the same deflator, the deflator cancels in the ratio. CHIP is identical whether or not wages are deflated.

This means the original study's deflation step was cosmetic for the final CHIP number. It affected the diagnostic columns (individual wages) but not the aggregate result. To produce a meaningful nominal series, we must explicitly **re-inflate** constant-dollar CHIP by the price level: `CHIP_nominal(Y) = CHIP_constant(Y) × deflator(Y) / deflator(base_year)`.

### 8.2 Real CHIP Is Approximately Stable

The timeseries study (PWT 10.0, 2000–2019) and production study (PWT 11.0, 2000–2022) both confirm that real (constant-dollar) CHIP fluctuates within a narrow range without a clear trend:

| Period | Source | Constant CHIP Range | Mean |
|--------|--------|-------------------|------|
| 2005–2019 (all countries) | Timeseries | $2.42–$3.25 | $2.89/hr |
| 2005–2019 (stable panel) | Timeseries | $3.25–$3.68 | $3.55/hr |
| 2005–2022 (all countries) | Production | $2.53–$3.16 | $2.85/hr |

This stability is consistent with the deflationary baseline argument (Section 5.2): the upward forces on labor value (rising living standards, opportunity cost) and the downward forces (automation, globalization) are roughly in balance. Real CHIP moves slowly—on the order of ±10% over a decade.

### 8.3 Nominal CHIP Tracks Inflation

Nominal CHIP rises over time, closely tracking cumulative US GDP deflator growth. The timeseries study found that nominal CHIP rose +95% from 2000 to 2019, while constant CHIP rose +41%, with the ~54% gap matching the cumulative deflator.

This finding is partly tautological (see Section 8.1—nominal = constant × deflator, by construction). But the practical implication is exactly what we want: **CHIP expressed in current dollars automatically adjusts for currency devaluation.** Users do not need to perform inflation calculations.

### 8.4 Composition Effects Drive Early Volatility

The number of countries with wage data grew from 5 (2000) to 64 (2018). This expansion drives large level shifts in the all-countries series, especially before 2005. The timeseries study identified a stable panel of 11 countries (PWT 10.0) or 10 countries (PWT 11.0) with consistent coverage. Within this panel, CHIP values are substantially less volatile.

### 8.5 Trailing Windows Work

The production study tested 1-year, 3-year, and 5-year trailing windows and found:

| Window | Mean Nominal | YoY Volatility |
|--------|-------------|----------------|
| 1-year | $2.58       | 20.1%          |
| 3-year | $2.58       | 6.8%           |
| 5-year | $2.57       | 5.0%           |

The 5-year window reduces volatility by 75% while preserving the long-run level. All windows converge to approximately the same mean, confirming that the windowing trades responsiveness for smoothness without introducing bias.

### 8.6 CPI Extrapolation Is Viable

The production study tested year-over-year CPI extrapolation (assuming real CHIP doesn't change) and found a mean correction of -0.7% with a standard deviation of 6.4%. During stable periods (2005–2018), corrections cluster around ±3–4%. During disruptions (COVID, 2019–2022), corrections reach ±12% year-over-year but are **mean-reverting**: the cumulative correction over the 2019–2022 COVID period was only about +6%.

This validates the approach used by chipcentral.net: extrapolate the last calculated CHIP forward using CPI, then correct when new data arrives.

### 8.7 Hypothesis Assessment

The hypotheses proposed in earlier drafts of this paper have now been tested:

| Hypothesis | Verdict | Evidence |
|-----------|---------|----------|
| H1: Nominal CHIP tracks inflation | **Confirmed** | Nominal series rises with deflator (timeseries study) |
| H2: Real CHIP is stable when composition is controlled | **Confirmed** | Stable panel constant CHIP std = $0.12 (timeseries study) |
| H3: Trailing window produces coherent series | **Confirmed** | 5-year window achieves 5.0% YoY volatility (production study) |
| H4: Recent-year CHIP is more actionable | **Confirmed** | 2022 nominal CHIP = $3.17, directly usable (production study) |

### 8.8 Current CHIP Estimate

As of the latest workbench run (PWT 11.0 data through 2022):

| Metric | Value |
|--------|-------|
| 2022 single-year, constant 2017$ | $2.69/hr |
| 2022 single-year, nominal | $3.17/hr |
| 2022 five-year trailing, nominal | $3.27/hr |
| Estimated February 2026 (CPI extrapolation) | ~$3.44–$3.55/hr |
| chipcentral.net (from original $2.53 × CPI) | $3.18/hr |

Our PWT 11.0 recalculation yields a higher base than the original study (~$2.84 in 2017 constant dollars vs ~$2.53), likely due to PWT data revisions, expanded country coverage, and MICE imputation. This gap compounds through CPI adjustment, placing the recommended current CHIP value approximately $0.30 above chipcentral.net's figure.

We view this directionally correct: CPI likely understates true inflation (substitution bias, quality adjustments), and to the extent that global living standards are rising, the real value of an hour of human labor may be increasing as well—consistent with the arguments in Section 5.5.

---

## 9. Conclusions

### 9.1 Summary of Findings

This analysis has established several key points:

First, **deflation cancels in the CHIP formula** and was unnecessary for the final CHIP value. The original study's deflation step, while standard academic practice, had no effect on the aggregate result. To produce nominal CHIP, we re-inflate constant-dollar CHIP by the price level.

Second, **CHIP should track inflation** when expressed in nominal terms. This is a feature, not a bug. A labor-based value index naturally rises with the nominal cost of labor. Empirical evidence from the workbench studies confirms this: nominal CHIP has risen roughly in line with the GDP deflator over 2000–2022.

Third, **real CHIP is approximately stable**. Constant-dollar CHIP fluctuates within a narrow range ($2.80–$3.15/hr for all countries, 2005–2022) without a clear upward or downward trend. The forces pushing labor value up and down are roughly in balance.

Fourth, **a 5-year trailing window** produces a smooth, defensible nominal CHIP series with 75% less year-over-year volatility than single-year estimates. CPI extrapolation between recalculations is viable, with corrections that are mean-reverting even through major disruptions like COVID.

Fifth, **the natural trajectory of prices is downward**, driven by technology and productivity growth. Monetary inflation masks this reality. CHIP, by anchoring to labor, strips away the monetary noise and reveals the underlying dynamics. In CHIP terms, most manufactured goods are getting cheaper; labor-intensive services hold steady; and genuinely scarce or artificially restricted goods reveal their real cost.

Sixth, **CHIP does not claim absolute stability**. If real economic changes (such as automation reducing demand for unskilled labor) cause labor value to decline relative to goods and capital, CHIP should reflect that decline. CHIP is chosen as an anchor because labor is universal and meaningful, not because it is immutable.

### 9.2 The Path Forward

The workbench studies have validated the core methodology. The remaining work is:

1. **Package the production methodology** into the `estimates/` pipeline for official CHIP calculation
2. **Complete the stability study** — compare PWT 10.0 vs 11.0 vintage differences and establish confidence bounds for update continuity
3. **Complete the weighting study** — assess sensitivity to GDP vs labor vs unweighted aggregation
4. **Update chipcentral.net** with the revised CHIP value from PWT 11.0 ($3.17 nominal for 2022, estimated ~$3.50 for 2026)
5. **Establish an annual update process** for MyCHIPs, with CPI extrapolation between full recalculations

### 9.3 The CHIP Value Proposition

By anchoring to labor rather than a basket of goods or precious metals, CHIP offers unique advantages as a value index:

**Stability without rigidity**: CHIP tracks the real, evolving value of human productive capacity rather than being fixed to an arbitrary historical level.

**Natural inflation tracking**: Nominal CHIP rises with labor costs, automatically adjusting for currency devaluation without requiring explicit inflation calculations.

**A window into real prices**: By stripping away monetary inflation, CHIP-denominated prices reveal which goods are genuinely getting cheaper (technology at work), which are holding steady (labor-intensive services), and which are getting more expensive (real scarcity or artificial distortion). This transparency is itself valuable—it helps users and policymakers distinguish real economic changes from monetary noise.

**Universal accessibility**: Everyone possesses their own supply of labor hours, making the CHIP standard intuitively meaningful across all cultures and economic systems.

**Resistance to manipulation**: While central banks can expand money supplies at will, the global supply of human labor-hours is bounded by population and biology. CHIP cannot be inflated by decree.

---

## References

- Bateman, K. (2022). *Got Choices*. https://gotchoices.org
- Baumol, W.J. (1967). "Macroeconomics of Unbalanced Growth: The Anatomy of Urban Crisis." *American Economic Review*, 57(3), 415-426.
- CHIP Definition. https://gotchoices.org/mychips/definition.html
- Feenstra, R.C., Inklaar, R., & Timmer, M.P. (2015). Penn World Table 10.0
- Feenstra, R.C., Inklaar, R., & Timmer, M.P. (2025). Penn World Table 11.0
- FRED Economic Data. US GDP Deflator (USAGDPDEFAISMEI)
- International Labour Organization. ILOSTAT Database. https://ilostat.ilo.org
- Solow, R.M. (1956). "A Contribution to the Theory of Economic Growth." *Quarterly Journal of Economics*, 70(1), 65-94.
