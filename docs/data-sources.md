# Data Sources

This document describes the external data sources used by the CHIP estimation
pipeline, their coverage, limitations, and alternatives.

---

## ILOSTAT (International Labour Organization)

**What it provides:** Country-level labor market data — employment counts,
wages, and hours worked — broken down by occupation using the ISCO
(International Standard Classification of Occupations) system.

**Why we need it:** ILOSTAT is the source of the "elementary wage" (unskilled
labor price) and the occupation-level detail needed to compute skill-weighted
effective labor. No other source provides global occupation-level wage data.

**API:** REST API at `https://rplumber.ilo.org/data/indicator/`

**Datasets used:**

| Dataset ID | Description | Key Columns |
|------------|-------------|-------------|
| `EMP_TEMP_SEX_OCU_NB_A` | Employment by occupation (annual) | country, year, ISCO code, count |
| `EAR_4HRL_SEX_OCU_CUR_NB_A` | Hourly earnings by occupation | country, year, ISCO code, currency, wage |
| `HOW_TEMP_SEX_OCU_NB_A` | Hours worked by occupation | country, year, ISCO code, hours |

**Coverage:**

| Dimension | Range |
|-----------|-------|
| Countries | ~230 territories (employment), ~134 (wages) |
| Years | 1969–present (employment), 1991–present (wages) |
| Update frequency | Continuous (as countries submit data) |

**Limitations:**

- **Wage data is the binding constraint.** Only 134 countries report
  occupation-level wages, and many have gaps. Employment coverage is much
  broader (208 countries).
- **Voluntary reporting.** Countries submit data on their own schedule. Some
  report annually, others intermittently. This drives the "composition effect"
  observed in the timeseries study (different countries present each year).
- **Unit inconsistency.** Wages are reported in local currency with varying
  units (hourly, monthly, annual). The pipeline filters to USD hourly wages
  (dataset `EAR_4HRL`), but this further reduces coverage.
- **ISCO version changes.** ISCO-88 was replaced by ISCO-08 around 2010–2012,
  potentially introducing discontinuities in occupation classification.

**Alternatives:** None for global occupation-level wage data. The OECD has
excellent wage statistics but only for ~38 member countries. The World Bank
has aggregate wage indicators but not at the occupation level needed for
skill-weighted effective labor.

---

## Penn World Tables (PWT)

**What it provides:** Cross-country comparable estimates of GDP, capital stock,
employment, human capital index, and labor share — all adjusted for purchasing
power parity (PPP). These are the macroeconomic inputs to the Cobb-Douglas
production function.

**Why we need it:** PWT provides the capital stock (K), GDP (Y), human capital
index (hc), and labor (L) needed to estimate the capital share (alpha) and the
marginal product of labor (MPL). Without PWT, the production-function approach
to CHIP estimation is not possible.

**Producer:** Groningen Growth and Development Centre (GGDC), University of
Groningen, Netherlands.

**Versions:**

| Version | Released | Coverage | Years | URL |
|---------|----------|----------|-------|-----|
| 10.0 | Jan 2021 | 183 countries | 1950–2019 | `https://www.rug.nl/ggdc/docs/pwt100.xlsx` |
| 10.01 | Feb 2023 | 183 countries | 1950–2019 | (minor fix to investment prices; no new years) |
| **11.0** | **Oct 2025** | **185 countries** | **1950–2023** | `https://dataverse.nl/api/access/datafile/554105` |

**Key columns used:**

| Column | Description |
|--------|-------------|
| `countrycode` | ISO 3-letter country code |
| `year` | Year |
| `rgdpna` | Real GDP at constant national prices (millions 2017 USD) |
| `rnna` | Capital stock at constant national prices (millions 2017 USD) |
| `emp` | Number of persons engaged (millions) |
| `hc` | Human capital index (based on years of schooling and returns to education) |
| `labsh` | Share of labor compensation in GDP |

**Why PWT is slow to update:** PWT depends on the World Bank's International
Comparison Program (ICP) for purchasing power parity benchmarks. The ICP
conducts comprehensive price surveys only every few years (2005, 2011, 2017,
2021). Each new ICP round triggers a PWT major version. Between ICP rounds,
PWT can only issue minor updates using extrapolated PPPs and updated national
accounts data.

PWT is **not discontinued** — version 11.0 was released in October 2025. But
the 2–4 year lag between data years and release is structural, driven by the
ICP dependency.

**Versioning in the workbench:** PWT data is cached by version. Studies can
pin a specific PWT version in their `config.yaml` to ensure reproducibility.
New studies default to the latest version. See `lib/fetcher.py` for details.

**Alternatives:**

- **World Bank World Development Indicators (WDI):** Has GDP and gross capital
  formation but not the constructed capital stock series PWT provides. Capital
  stock is estimated by PWT using a perpetual inventory method, which is not
  trivial to replicate.
- **Global Macro Database (GMD):** A newer aggregation of 111 sources covering
  240 countries through 2024 with forecasts to 2030. Includes GDP and some
  capital metrics. Could potentially supplement PWT for the bridge period
  (years beyond PWT coverage). Available via Python/R packages. Free for
  non-commercial academic use. Worth evaluating for the `production` study.
- **IMF World Economic Outlook (WEO):** Has GDP estimates and forecasts by
  country. Could be used for GDP extrapolation in the bridge period, but does
  not have capital stock.
- **OECD Productivity Statistics:** Capital stock estimates for OECD members.
  Good coverage but limited to ~38 countries.

---

## FRED (Federal Reserve Economic Data)

**What it provides:** The US GDP deflator, used to convert between nominal
(current-year) and constant (base-year) dollars.

**Why we need it:** The deflator adjusts wage data for inflation when
computing constant-dollar CHIP. It is also used to re-inflate constant CHIP
to produce a nominal series, and for CPI-based extrapolation between
recalculations.

**API:** Two access methods:
- **With API key:** `https://api.stlouisfed.org/fred/series/observations?series_id=USAGDPDEFAISMEI&api_key=KEY&file_type=json`
- **Public CSV (no key):** `https://fred.stlouisfed.org/graph/fredgraph.csv?id=USAGDPDEFAISMEI`

**Series used:** `USAGDPDEFAISMEI` (GDP Implicit Price Deflator, USA, annual)

**Coverage:** 1960–present, updated quarterly with approximately one quarter
of lag. Effectively real-time for our annual purposes.

**Alternatives:** Any US price index would work in principle:

| Index | Source | Notes |
|-------|--------|-------|
| GDP Deflator | FRED | Current choice; broadest price measure |
| CPI-U | BLS/FRED | Consumer prices; more familiar to users |
| PCE Deflator | BEA/FRED | Fed's preferred inflation measure |
| World Bank GDP Deflator | WDI | Country-specific deflators available |

For the production pipeline, CPI may be more appropriate for user-facing
extrapolation (it's published monthly and is what people think of as
"inflation"), while the GDP deflator remains better for the core deflation
methodology.

---

## Data Flow Summary

```
ILOSTAT                     PWT                         FRED
  │                          │                            │
  ├─ Employment (208 ctry)   ├─ GDP (rgdpna)              └─ GDP Deflator
  ├─ Wages (134 ctry)        ├─ Capital stock (rnna)
  └─ Hours (170 ctry)        ├─ Employment (emp)
                             ├─ Human capital (hc)
                             └─ Labor share (labsh)
         │                          │                       │
         └──────────┬───────────────┘                       │
                    │                                       │
              CHIP Pipeline                                 │
              (lib/pipeline.py)  ◄──────────────────────────┘
                    │
              CHIP estimate ($/hr)
```

**Binding constraints:**

1. **Wage coverage** limits which countries can contribute to CHIP (134 of 230)
2. **PWT release cycle** limits how recent our calculated estimates can be
   (currently 2023 with PWT 11.0)
3. **Country reporting consistency** drives year-to-year composition effects

---

## Updating Data Sources

### Routine refresh (any time)

```bash
cd workbench
rm -rf data/          # Delete cache
./run.sh baseline     # Auto-fetches fresh data
```

ILOSTAT and FRED data is always fetched at the latest version. PWT is fetched
at the version specified in the study's config (or the default).

### PWT version upgrade

When a new PWT version is released:

1. Add the new version URL to `lib/fetcher.py` in the `PWT_VERSIONS` dict
2. Update `PWT_DEFAULT_VERSION` to the new version
3. New studies will automatically use the new version
4. Existing completed studies retain their pinned version
5. To re-run an existing study with new PWT data, update its `config.yaml`:
   ```yaml
   data:
     pwt_version: "11.0"
   ```

---

## References

- ILO. ILOSTAT Database. https://ilostat.ilo.org
- Feenstra, R.C., Inklaar, R., & Timmer, M.P. (2015). "The Next Generation of
  the Penn World Table." *American Economic Review*, 105(10), 3150-3182.
- PWT 11.0. https://www.rug.nl/ggdc/productivity/pwt/
- FRED Economic Data. https://fred.stlouisfed.org
- Global Macro Database. https://www.globalmacrodata.com/
