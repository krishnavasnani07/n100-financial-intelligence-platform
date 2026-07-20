# Cash Flow Analytics Engine — Architectural Design & Specification

## 📌 Overview
The **Cash Flow Analytics Engine** (`src/analytics/cashflow_kpis.py`) provides specialized cash flow metrics and pattern-based capital allocation classification for the Nifty 100 Financial Intelligence Platform.

---

## 🏗️ Engine Architecture & Components

```text
SQLite Database (nifty100.db)
       │
       ▼ (JOIN cashflow & profitandloss)
CashFlowEngine.compute_company_cashflow_kpis()
       │
       ├──► Free Cash Flow (FCF) = OCF + ICF
       ├──► 5-Year Rolling CFO Quality = Avg(OCF / PAT)
       ├──► CapEx Intensity = (|ICF| / Sales) * 100
       ├──► FCF Conversion = FCF / Operating Profit
       └──► Capital Allocation Pattern Matcher (3-Sign Matrix)
       │
       ▼
CSV Export Layer (output/capital_allocation.csv & summary tables)
```

---

## 📊 Benchmark Thresholds & Classification Matrix

### 1. CFO Quality Score
- **Formula**: $\frac{\text{Operating Cash Flow}}{\text{Net Profit}}$ (5-Year Average)
- **High Quality**: $> 1.0$
- **Moderate Quality**: $0.5 - 1.0$
- **Accrual Risk**: $< 0.5$

### 2. CapEx Intensity
- **Formula**: $\frac{|\text{Investing Cash Flow}|}{\text{Sales Revenue}} \times 100$
- **Asset Light**: $< 3\%$
- **Moderate Intensity**: $3\% - 8\%$
- **Capital Intensive**: $> 8\%$

### 3. Capital Allocation Pattern Matrix (8 Archetypes)
| OCF | ICF | FCF | Pattern Label | Special Business Conditions |
| :---: | :---: | :---: | :--- | :--- |
| $+$ | $-$ | $-$ | **Reinvestor** | CFO / PAT $\le 1.0$ |
| $+$ | $-$ | $-$ | **Shareholder Returns** | CFO / PAT $> 1.0$ |
| $+$ | $+$ | $-$ | **Liquidating Assets** | Proceeds from asset sales return capital |
| $-$ | $+$ | $+$ | **Distress Signal** | Operating loss covered by asset sale & debt |
| $-$ | $-$ | $+$ | **Growth Funded by Debt** | Operating & CapEx deficits funded externally |
| $+$ | $+$ | $+$ | **Cash Accumulator** | Operations & financing inflows stored as cash |
| $-$ | $-$ | $-$ | **Pre-Revenue** | Early-stage/R&D operational & CapEx burn |
| $+$ | $-$ | $+$ | **Mixed** | Reinvestment & external funding combination |
