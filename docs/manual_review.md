# Manual Data Quality Review & Audit Documentation (Sprint 1 - Day 6)

## 📌 Overview
This document logs the manual quality assurance audit conducted across 5 sample companies representing diverse economic sectors in the Nifty 100 universe. The audit verifies data parity across three pipeline stages: **Raw Excel Files $\rightarrow$ Normalized In-Memory DataFrames $\rightarrow$ SQLite Relational Database**.

---

## 🏢 Selected Sample Companies

| Ticker | Company Name | Sector Category | Selection Rationale |
| :--- | :--- | :--- | :--- |
| **TCS** | Tata Consultancy Services Ltd | Information Technology | High-volume IT services benchmark |
| **HDFCBANK** | HDFC Bank Ltd | Financials (Banking) | Large-cap banking balance sheet structure |
| **ITC** | ITC Ltd | Consumer Staples (FMCG) | Consumer goods & diversified conglomerate |
| **TATAMOTORS** | Tata Motors Ltd | Consumer Discretionary (Auto) | High capital expenditure & global auto maker |
| **SUNPHARMA** | Sun Pharmaceuticals Industries Ltd | Healthcare (Pharma) | Major pharmaceutical & R&D enterprise |

---

## 🔍 Stage-by-Stage Value Matching Matrix (Financial Year: Mar 2023)

### 1. Tata Consultancy Services Ltd (`TCS`)
- **Master Metadata Verification**: Name = `Tata Consultancy Services Ltd`, Sector = `Information Technology`, Company ID = `TCS`.
- **Relational Row References**: `companies`: 1 | `sectors`: 1 | `profitandloss`: 13 | `balancesheet`: 13 | `cashflow`: 24 | `documents`: 16.
- **Financial Field Match Matrix**:
  | Financial Field | Raw Excel Value | SQLite Stored Value | Match Status | Discrepancy / Notes |
  | :--- | :--- | :--- | :--- | :--- |
  | **Sales Revenue** | 225458 | 225458.0 | ✅ 100% Match | Direct numeric precision |
  | **Net Profit** | 42303 | 42303.0 | ✅ 100% Match | Direct numeric precision |
  | **Equity Capital** | 366.0 | 366.0 | ✅ 100% Match | Direct numeric precision |
  | **Total Assets** | 142859 | 142859.0 | ✅ 100% Match | Direct numeric precision |

### 2. HDFC Bank Ltd (`HDFCBANK`)
- **Master Metadata Verification**: Name = `HDFC Bank Ltd`, Sector = `Financials`, Company ID = `HDFCBANK`.
- **Relational Row References**: `companies`: 1 | `sectors`: 1 | `profitandloss`: 13 | `balancesheet`: 12 | `cashflow`: 12 | `documents`: 16.
- **Financial Field Match Matrix**:
  | Financial Field | Raw Excel Value | SQLite Stored Value | Match Status | Discrepancy / Notes |
  | :--- | :--- | :--- | :--- | :--- |
  | **Sales Revenue** | 170754 | 170754.0 | ✅ 100% Match | Direct numeric precision |
  | **Net Profit** | 46149 | 46149.0 | ✅ 100% Match | Direct numeric precision |
  | **Equity Capital** | 558.0 | 558.0 | ✅ 100% Match | Direct numeric precision |
  | **Total Assets** | 2530432 | 2530432.0 | ✅ 100% Match | Direct numeric precision |

### 3. ITC Ltd (`ITC`)
- **Master Metadata Verification**: Name = `ITC Ltd`, Sector = `Consumer Staples`, Company ID = `ITC`.
- **Relational Row References**: `companies`: 1 | `sectors`: 1 | `profitandloss`: 13 | `balancesheet`: 13 | `cashflow`: 12 | `documents`: 16.
- **Financial Field Match Matrix**:
  | Financial Field | Raw Excel Value | SQLite Stored Value | Match Status | Discrepancy / Notes |
  | :--- | :--- | :--- | :--- | :--- |
  | **Sales Revenue** | 70919 | 70919.0 | ✅ 100% Match | Direct numeric precision |
  | **Net Profit** | 19477 | 19477.0 | ✅ 100% Match | Direct numeric precision |
  | **Equity Capital** | 1243.0 | 1243.0 | ✅ 100% Match | Direct numeric precision |
  | **Total Assets** | 85831 | 85831.0 | ✅ 100% Match | Direct numeric precision |

### 4. Tata Motors Ltd (`TATAMOTORS`)
- **Master Metadata Verification**: Name = `Tata Motors Ltd`, Sector = `Consumer Discretionary`, Company ID = `TATAMOTORS`.
- **Relational Row References**: `companies`: 1 | `sectors`: 1 | `profitandloss`: 13 | `balancesheet`: 13 | `cashflow`: 12 | `documents`: 16.
- **Financial Field Match Matrix**:
  | Financial Field | Raw Excel Value | SQLite Stored Value | Match Status | Discrepancy / Notes |
  | :--- | :--- | :--- | :--- | :--- |
  | **Sales Revenue** | 345967 | 345967.0 | ✅ 100% Match | Direct numeric precision |
  | **Net Profit** | 2690 | 2690.0 | ✅ 100% Match | Direct numeric precision |
  | **Equity Capital** | 766.0 | 766.0 | ✅ 100% Match | Direct numeric precision |
  | **Total Assets** | 334674 | 334674.0 | ✅ 100% Match | Direct numeric precision |

### 5. Sun Pharmaceuticals Industries Ltd (`SUNPHARMA`)
- **Master Metadata Verification**: Name = `Sun Pharmaceuticals Industries Ltd`, Sector = `Healthcare`, Company ID = `SUNPHARMA`.
- **Relational Row References**: `companies`: 1 | `sectors`: 1 | `profitandloss`: 13 | `balancesheet`: 13 | `cashflow`: 12 | `documents`: 16.
- **Financial Field Match Matrix**:
  | Financial Field | Raw Excel Value | SQLite Stored Value | Match Status | Discrepancy / Notes |
  | :--- | :--- | :--- | :--- | :--- |
  | **Sales Revenue** | 43886 | 43886.0 | ✅ 100% Match | Direct numeric precision |
  | **Net Profit** | 8513 | 8513.0 | ✅ 100% Match | Direct numeric precision |
  | **Equity Capital** | 240.0 | 240.0 | ✅ 100% Match | Direct numeric precision |
  | **Total Assets** | 80712 | 80712.0 | ✅ 100% Match | Direct numeric precision |

---

## 📊 Year Coverage & Historical Depth Analysis
- **Total Master Companies Evaluated**: 92
- **Companies with Complete Historical History ($\ge 5$ years)**: 91 / 92 (98.9%)
- **Companies with $< 5$ Years Coverage**: 1 company (`JIOFIN` - newly listed entity with recent spin-off history).
- **Year Coverage CSV Export**: Available at `output/reports/year_coverage.csv`.
