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
