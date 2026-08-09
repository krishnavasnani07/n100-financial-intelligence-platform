# Financial Analytics & Calculation Methodology

This document details the analytical models, scoring rubrics, and math formulas computed by the Nifty 100 Financial Intelligence Engines.

## 1. Compound Annual Growth Rate (CAGR)

CAGR represents the annualized growth rate of a financial metric (Revenue, PAT, EPS, or FCF) over a specified period:

$$\text{CAGR} = \left(\frac{\text{End Value}}{\text{Start Value}}\right)^{\frac{1}{n}} - 1$$

Where:
- $n$: Number of years (typically 3 or 5).
- $\text{Start Value}$: Starting year metric.
- $\text{End Value}$: Ending year metric.

### Edge Case Handling:
- **Zero or Negative Values**: Standard CAGR calculations fail when values transition between positive and negative numbers.
- **Decline to Loss**: If $\text{Start Value} > 0$ and $\text{End Value} \le 0$, CAGR is designated as `-100%`.
- **Turnaround (Recovery)**: If $\text{Start Value} \le 0$ and $\text{End Value} > 0$, CAGR is designated as `+100%` to signify recovery.
- **Both Negative**: If both are negative, CAGR is flagged as `N/A` (Not Available).

---

## 2. Free Cash Flow (FCF) Yield

FCF Yield evaluates the cash-generative power of a firm relative to its total market value:

$$\text{FCF Yield \%} = \left(\frac{\text{Free Cash Flow}}{\text{Market Capitalization}}\right) \times 100$$

Where:
- $\text{Free Cash Flow}$: Operating Cash Flow minus Capital Expenditures (CapEx).
- $\text{Market Capitalization}$: Current price per share times the total outstanding shares.

---

## 3. Composite Quality Score

The Composite Quality Score ranks the 92 companies within their respective sectors to select high-performing assets. It integrates multiple sub-metrics:

1. **ROE Score** (Return on Equity)
2. **ROCE Score** (Return on Capital Employed)
3. **NPM Score** (Net Profit Margin)
4. **FCF CAGR Score**
5. **CFO/PAT Score** (Cash Flow from Operations relative to Net Profit)
6. **Debt-to-Equity Score** (Penalizes excessive leverage)
7. **Interest Coverage Score**

### Relative Percentile Normalization:
For each metric, values are converted to sector-relative percentiles:

$$\text{Percentile} = \frac{\text{Rank of Company in Sector}}{\text{Total Companies in Sector}} \times 100$$

Scores are winsorized to eliminate outlier skewness, and averaged to form the **Composite Quality Score (CQS)**, ranging from `0` (lowest quality) to `100` (highest quality).

---

## 4. Valuation Flags

The system dynamically categorizes valuation by comparing a company's current P/E Ratio to its Sector Median P/E:

$$\text{PE Ratio vs Sector Median \%} = \left(\frac{\text{Company P/E}}{\text{Sector Median P/E}}\right) \times 100$$

### Categorization Thresholds:
- **Discount**: $\text{PE vs Sector Median \%} < 70\%$ (Under-valued relative to peers).
- **Caution**: $\text{PE vs Sector Median \%} > 150\%$ (Over-valued relative to peers).
- **Fair**: $70\% \le \text{PE vs Sector Median \%} \le 150\%$.
