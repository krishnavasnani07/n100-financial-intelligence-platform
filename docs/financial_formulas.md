# Financial Formula Specification & KPI Reference Guide

## 📌 Executive Summary
This document serves as the authoritative formula reference manual for the Nifty 100 Financial Intelligence Platform. It defines each profitability KPI, its mathematical formulation, underlying data tables, edge-case rules, and interpretation guidelines.

---

## 📐 KPI Formula Reference Table

| KPI Identifier | Full Ratio Name | Mathematical Formula | Source Datasets | Edge Case Handling | Default Benchmark |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NPM** | Net Profit Margin | $\frac{\text{Net Profit}}{\text{Sales}} \times 100$ | `profitandloss` | Returns `None` if Sales $\le 0$ | $\ge 15\%$ (Excellent) |
| **OPM** | Operating Profit Margin | $\frac{\text{Operating Profit}}{\text{Sales}} \times 100$ | `profitandloss` | Cross-checks reported OPM; logs anomaly if diff $>1.0\%$ | $\ge 25\%$ (Excellent) |
| **ROE** | Return on Equity | $\frac{\text{Net Profit}}{\text{Equity Capital} + \text{Reserves}} \times 100$ | `profitandloss` + `balancesheet` | Returns `None` if Total Equity $\le 0$ | $\ge 20\%$ (Excellent) |
| **ROCE** | Return on Capital Employed | $\frac{\text{EBIT}}{\text{Equity} + \text{Reserves} + \text{Borrowings}} \times 100$ | `profitandloss` + `balancesheet` | Returns `None` if Capital $\le 0$; flags Financial sector entities | $\ge 20\%$ (Excellent) |
| **ROA** | Return on Assets | $\frac{\text{Net Profit}}{\text{Total Assets}} \times 100$ | `profitandloss` + `balancesheet` | Returns `None` if Total Assets $\le 0$ | $\ge 15\%$ (Excellent) |
| **D/E** | Debt-to-Equity | $\frac{\text{Borrowings}}{\text{Equity Capital} + \text{Reserves}}$ | `balancesheet` | Borrowings $=0 \rightarrow 0$; Equity $\le 0 \rightarrow \text{None}$; High Leverage Flag if $> 5.0$ (Non-Financials) | $\le 0.5$ (Healthy) |
| **ICR** | Interest Coverage Ratio | $\frac{\text{Operating Profit} + \text{Other Income}}{\text{Interest Expense}}$ | `profitandloss` | Interest $=0 \rightarrow \text{None} + \text{"Debt Free"}$; Warning Flag if $< 1.5$ | $\ge 5.0$ (Strong) |
| **Net Debt** | Net Debt | $\text{Borrowings} - \text{Investments}$ | `balancesheet` | Negative values allowed (indicates net cash / liquid surplus) | $\le 0$ (Ideal) |
| **Asset Turnover** | Asset Turnover | $\frac{\text{Sales}}{\text{Total Assets}}$ | `profitandloss` + `balancesheet` | Returns `None` if Total Assets $\le 0$ | $\ge 1.5$ (Excellent) |
| **Revenue CAGR** | Revenue Growth Rate | $\left[\left(\frac{\text{Sales}_T}{\text{Sales}_0}\right)^{\frac{1}{T}} - 1\right] \times 100$ | `profitandloss` | 6 Financial Edge Cases (Zero base, turnaround, decline to loss, etc.) | $> 10\%$ (Strong Growth) |
| **PAT CAGR** | Net Profit Growth Rate | $\left[\left(\frac{\text{PAT}_T}{\text{PAT}_0}\right)^{\frac{1}{T}} - 1\right] \times 100$ | `profitandloss` | 6 Financial Edge Cases (Zero base, turnaround, decline to loss, etc.) | $> 10\%$ (Strong Growth) |
| **EPS CAGR** | EPS Growth Rate | $\left[\left(\frac{\text{EPS}_T}{\text{EPS}_0}\right)^{\frac{1}{T}} - 1\right] \times 100$ | `profitandloss` | 6 Financial Edge Cases (Zero base, turnaround, decline to loss, etc.) | $> 10\%$ (Strong Growth) |
| **FCF** | Free Cash Flow | $\text{CFO} + \text{CFI}$ | `cashflow` | CFI is negative; negative FCF valid and unadjusted | $> 0$ (Ideal) |
| **CFO Quality** | CFO Quality Score | $\frac{\text{CFO}}{\text{PAT}}$ (5-yr Avg) | `cashflow` + `profitandloss` | Returns `None` if PAT $\le 0$ | $> 1.0$ (High Quality) |
| **CapEx Intensity** | CapEx Intensity | $\frac{|\text{CFI}|}{\text{Sales}} \times 100$ | `cashflow` + `profitandloss` | Returns `None` if Sales $\le 0$ | $< 3\%$ (Asset Light) |
| **FCF Conversion** | FCF Conversion Ratio | $\frac{\text{FCF}}{\text{Operating Profit}}$ | `cashflow` + `profitandloss` | Returns `None` if Operating Profit $\le 0$ | $> 0.8$ (High Conversion) |
| **Capital Allocation** | Capital Allocation Pattern | Sign Matrix $(\text{CFO}, \text{CFI}, \text{CFF})$ | `cashflow` + `profitandloss` | 8 distinct allocation archetypes (Reinvestor, Shareholder Returns, etc.) | N/A (Categorical) |

---

## 🔍 Detailed KPI Specifications

### 1. Net Profit Margin (NPM)
- **Business Purpose**: Measures bottom-line profitability generated per rupee of revenue.
- **Formula**:
  $$\text{NPM} = \frac{\text{Net Profit}}{\text{Sales Revenue}} \times 100$$
- **Edge Cases**: Zero or negative sales returns `None` (status: `NON_POSITIVE_SALES`).

### 2. Operating Profit Margin (OPM)
- **Business Purpose**: Evaluates core operational efficiency prior to financing costs and taxation.
- **Formula**:
  $$\text{OPM} = \frac{\text{Operating Profit}}{\text{Sales Revenue}} \times 100$$
- **Validation Rule**: If raw source file includes `opm_percentage`, computed OPM is cross-checked. Discrepancies $>1.0\%$ trigger an anomaly log warning.

### 3. Return on Equity (ROE)
- **Business Purpose**: Measures the rate of return earned on shareholder capital.
- **Formula**:
  $$\text{ROE} = \frac{\text{Net Profit}}{\text{Equity Capital} + \text{Reserves \& Surplus}} \times 100$$
- **Edge Cases**: If Total Equity $\le 0$ (distressed balance sheet), ROE is suppressed to `None` to prevent misleading positive ratios from negative net profits.

### 4. Return on Capital Employed (ROCE)
- **Business Purpose**: Evaluates overall capital efficiency across both debt and equity providers.
- **Formula**:
  $$\text{ROCE} = \frac{\text{Operating Profit (EBIT)}}{\text{Equity Capital} + \text{Reserves} + \text{Total Borrowings}} \times 100$$
- **Financial Sector Exception**: Banks and NBFCs leverage deposits as operating capital rather than long-term debt; ROCE is flagged for sector-relative evaluation.

### 5. Return on Assets (ROA)
- **Business Purpose**: Measures asset utilization efficiency in generating net profits.
- **Formula**:
  $$\text{ROA} = \frac{\text{Net Profit}}{\text{Total Assets}} \times 100$$
- **Edge Cases**: Returns `None` if Total Assets $\le 0$.

### 6. Debt-to-Equity (D/E)
- **Business Purpose**: Measures financial leverage and solvency risk relative to equity capital.
- **Formula**:
  $$\text{D/E} = \frac{\text{Borrowings}}{\text{Equity Capital} + \text{Reserves}}$$
- **Edge Cases**: Returns `0` if borrowings equal zero. Returns `None` if equity capital + reserves $\le 0$. Triggers `high_leverage_flag = True` if D/E $> 5.0$ for non-financial companies.

### 7. Interest Coverage Ratio (ICR)
- **Business Purpose**: Evaluates the company's ability to comfortably service its interest obligations from operational earnings.
- **Formula**:
  $$\text{ICR} = \frac{\text{Operating Profit} + \text{Other Income}}{\text{Interest Expense}}$$
- **Edge Cases**: Interest $= 0$ suppresses ICR calculation to `None` and assigns `icr_label = "Debt Free"`. Triggers `icr_warning = True` if ICR $< 1.5$.

### 8. Net Debt
- **Business Purpose**: Measures net debt liability taking into account liquid investment assets that could offset debt.
- **Formula**:
  $$\text{Net Debt} = \text{Borrowings} - \text{Investments}$$
- **Edge Cases**: Negative Net Debt is valid and unadjusted, indicating a cash-surplus balance sheet.

### 9. Asset Turnover
- **Business Purpose**: Evaluates the efficiency of asset utilization in generating top-line sales revenue.
- **Formula**:
  $$\text{Asset Turnover} = \frac{\text{Sales Revenue}}{\text{Total Assets}}$$
- **Edge Cases**: Returns `None` if Total Assets $\le 0$.

### 10. Compound Annual Growth Rate (CAGR) Engine
- **Business Purpose**: Evaluates smoothed annual growth rate of financial metrics (Revenue, PAT, EPS) over 3-year, 5-year, and 10-year time windows.
- **Formula**:
  $$\text{CAGR} = \left[\left(\frac{\text{End Value}}{\text{Start Value}}\right)^{\frac{1}{\text{Years}}} - 1\right] \times 100$$

- **Financial Edge Cases Handling**:
  1. **Positive $\rightarrow$ Positive**: Normal calculation. Returns CAGR %, Flag: `VALID`.
  2. **Positive $\rightarrow$ Negative / Zero**: Company moved from profit/revenue to loss or zero. Returns `None`, Flag: `DECLINE_TO_LOSS`.
  3. **Negative $\rightarrow$ Positive**: Loss-making company turned profitable. Formula generates mathematically invalid/misleading negative CAGR. Returns `None`, Flag: `TURNAROUND`.
  4. **Negative $\rightarrow$ Negative / Zero**: Loss persisted across periods. Returns `None`, Flag: `BOTH_NEGATIVE`.
  5. **Zero Base**: Initial base value was zero ($0 \rightarrow X$). Division by zero. Returns `None`, Flag: `ZERO_BASE`.
  6. **Insufficient Data**: Missing historical year record or non-positive year period. Returns `None`, Flag: `INSUFFICIENT`.

- **Growth Tiers Classification**:
  - $> 20\%$: **High Growth**
  - $10\% - 20\%$: **Strong Growth**
  - $5\% - 10\%$: **Moderate**
  - $0\% - 5\%$: **Slow**
  - $< 0\%$: **Declining**
  - Edge Cases / Suppressed: **N/A**

### 11. Cash Flow Analytics & Capital Allocation Engine
- **Business Purpose**: Analyzes cash generation, cash quality, capital intensity, cash conversion efficiency, and classifies corporate capital allocation patterns across 8 distinct business archetypes.

#### A. Free Cash Flow (FCF)
- **Formula**: $\text{FCF} = \text{Operating Cash Flow (CFO)} + \text{Investing Cash Flow (CFI)}$
- **Notes**: Investing cash flow is typically negative (CapEx/investments). Negative FCF is completely valid and unadjusted.

#### B. CFO Quality Score
- **Formula**: $\text{CFO Quality} = \frac{\text{Operating Cash Flow (CFO)}}{\text{Net Profit (PAT)}}$ (averaged over 5 years).
- **Classification**:
  - $> 1.0$: **High Quality** (Strong cash conversion of reported accounting profits)
  - $0.5 - 1.0$: **Moderate**
  - $< 0.5$: **Accrual Risk** (Earnings supported primarily by non-cash working capital accruals)
- **Edge Cases**: Suppressed to `None` if Net Profit $\le 0$.

#### C. CapEx Intensity
- **Formula**: $\text{CapEx Intensity (\%)} = \frac{|\text{Investing Cash Flow (CFI)}|}{\text{Sales}} \times 100$
- **Classification**:
  - $< 3\%$: **Asset Light**
  - $3\% - 8\%$: **Moderate**
  - $> 8\%$: **Capital Intensive**
- **Edge Cases**: Suppressed to `None` if Sales $\le 0$.

#### D. FCF Conversion Ratio
- **Formula**: $\text{FCF Conversion} = \frac{\text{Free Cash Flow (FCF)}}{\text{Operating Profit}}$
- **Edge Cases**: Suppressed to `None` if Operating Profit $\le 0$.

#### E. Capital Allocation Classifier (8 Patterns)
- **Methodology**: Evaluates the mathematical signs $(+, -)$ of Operating Cash Flow ($\text{CFO}$), Investing Cash Flow ($\text{CFI}$), and Financing Cash Flow ($\text{CFF}$).

| CFO Sign | CFI Sign | CFF Sign | Pattern Label | Business Interpretation |
| :---: | :---: | :---: | :--- | :--- |
| $+$ | $-$ | $-$ | **Reinvestor** | Cash from operations reinvested in growth with balance returned to debt/equity (CFO/PAT $\le 1.0$) |
| $+$ | $-$ | $-$ | **Shareholder Returns** | High CFO quality (CFO/PAT $> 1.0$) with heavy capital return via dividends/buybacks/debt reduction |
| $+$ | $+$ | $-$ | **Liquidating Assets** | Operating cash and asset sale proceeds used to reduce debt or return capital |
| $-$ | $+$ | $+$ | **Distress Signal** | Operating cash burn compensated by asset liquidation and external financing |
| $-$ | $-$ | $+$ | **Growth Funded by Debt** | Operating cash deficit and capital expenditures funded by debt/equity capital |
| $+$ | $+$ | $+$ | **Cash Accumulator** | Operations, asset sales, and financing inflows accumulated in liquid reserves |
| $-$ | $-$ | $-$ | **Pre-Revenue** | Early-stage/R&D cash burn across operations, capital investments, and financing outflows |
| $+$ | $-$ | $+$ | **Mixed** | Positive operating cash flow combined with external debt/equity capital raising and investment |



