# Contributing to N100 Financial Intelligence Platform

Thank you for choosing to contribute to our flagship platform! This guide outlines developer onboarding, coding guidelines, testing, and contribution protocols to help you get started in under 15 minutes.

---

## 🚀 1. Quick Setup & Onboarding

Get the project running locally using our platform automation scripts:

### Windows:
```cmd
# 1. Run environment initialization and dependency setup
setup.bat

# 2. Run the test suite to verify the installation
test.bat

# 3. Ingest files, run validation rules, and run Streamlit dashboard
run.bat
```

### macOS / Linux:
```bash
# 1. Run environment initialization and dependency setup
chmod +x *.sh
./setup.sh

# 2. Run the test suite to verify the installation
./test.sh

# 3. Ingest files, run validation rules, and run Streamlit dashboard
./run.sh
```

---

## 📂 2. Project Layout

```text
n100-financial-intelligence-platform/
├── config/                  # Ingestion & ratio YAML configs
├── data/                    # Local Excel data (ignored in Git)
├── db/                      # SQLite DB, backups, and schema.sql
├── docs/                    # Architectural documents
├── src/                     # Application Source Code
│   ├── analytics/           # Ratios, CAGR, cash flow engines
│   ├── config/              # Central configuration & settings
│   ├── database/            # Connection managers & query helpers
│   ├── etl/                 # Normalizers and loaders
│   ├── peer_analysis/       # Peer ranks and averaging metrics
│   ├── screener/            # Preset filter engines
│   ├── utils/               # PDF reports & AI insights
│   └── validation/          # 16 Data Quality rules
├── tests/                   # 279-test Pytest suite
├── app.py                   # Streamlit Dashboard UI
└── main.py                  # Ingestion Pipeline Runner
```

---

## 💡 3. Development Workflow

### Data Quality Rules (DQ Rules)
If you want to add or modify data quality constraints:
1. Open the rule schema configurations in `config/screener_rules.yaml`.
2. Add your check to `src/validation/validator.py` under the corresponding DQ identifier (e.g., `DQ-17`).
3. Create corresponding unit tests in `tests/validation/` to ensure your checks work cleanly.

### Code Style & Quality Standards
Before submitting changes, run the linter utility script:
* **Windows**: `lint.bat`
* **macOS / Linux**: `./lint.sh`

Ensure that:
* **Type Safety**: Type hints are added to all public functions.
* **Error Handling**: Graceful exceptions are caught and logged, rather than leaking traceback prints to console users.
* **Logging**: Structured logger messages are printed at appropriate levels (e.g., warnings for invalid cells, info for successful stages).
* **Settings**: Hardcoded paths are avoided. Centralize configuration variables in `src/config/settings.py` and load them via `.env`.

---

## 🧪 4. Testing Guidelines

Our platform requires 100% compliance with our Pytest suite. Always write tests for new components or bug fixes:
* Place tests under `tests/` matching the subfolder of the target code.
* Execute `test.bat` (or `./test.sh`) to run the full suite.
* Ensure all tests pass green before proposing commits.
