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

