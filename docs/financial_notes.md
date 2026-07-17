# Financial Analyst Notes & Domain Considerations

## 💡 Key Financial Interpretation Nuances

### 1. High ROE vs Financial Leverage Risk
- A high ROE does not always signify superior operational performance.
- Companies with aggressive debt loads reduce shareholder equity, artificially inflating ROE ($\text{ROE} = \text{ROA} \times \text{Financial Leverage}$).
- **Analyst Rule**: Always evaluate ROE alongside Debt-to-Equity and ROCE.

### 2. Banking & Financial Sector Anomalies
- Traditional balance sheet ratios (e.g. Debt-to-Equity, ROCE) behave differently for banking institutions (`HDFCBANK`, `ICICIBANK`, `SBIN`).
- Customer deposits are classified as liabilities, making traditional capital employed metrics artificially low or distorted.
- **Analyst Rule**: Use Return on Assets (ROA) and Net Interest Margin (NIM) for financial sector entities.

### 3. Negative Equity Distortions
- Distressed entities or companies undergoing restructuring may report negative total equity (`Equity + Reserves < 0`).
- Dividing negative Net Profit by negative Equity yields a mathematically positive ROE, which creates a false positive signal.
- **Engine Rule**: The ratio engine suppresses ROE to `None` whenever Total Equity $\le 0$.
