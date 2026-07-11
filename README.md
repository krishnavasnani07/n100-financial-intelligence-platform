# Nifty 100 Financial Intelligence Platform

A modular, robust financial data engineering and intelligence pipeline designed to ingest, process, store, and analyze market data for the Nifty 100 companies.

## 📁 Project Architecture

```text
n100-financial-intelligence-platform/
│
├── assets/                  # Visual assets, charts, and media
│
├── data/                    # Multi-stage data lake
│   ├── raw/                 # Raw ingestion layer (Excel files)
│   ├── processed/           # Transformed & cleaned data
│   └── external/            # External lookup and mapping files
│
├── db/                      # Database storage & schemas
│   ├── schema.sql           # SQLite database schema
│   └── nifty100.db          # Active SQLite database file
│
├── docs/                    # Project documentation
│
├── notebooks/               # Research & EDA Jupyter Notebooks
│
├── output/                  # Pipeline outputs
│   ├── audit/               # Data quality audit logs
│   ├── reports/             # Generated PDF/HTML financial reports
│   └── validation/          # Validation schemas and results
│
├── reports/                 # Analysis and presentation artifacts
│
├── src/                     # Source code package
│   ├── config/              # Application configuration
│   │   └── settings.py      # Day 2: Central settings & path resolution
│   ├── etl/                 # Ingestion & Transformation pipelines
│   │   ├── loader.py        # Day 2: Generic Excel loader
│   │   └── normalizer.py    # Day 2: Data normalizers (years/tickers)
│   ├── utils/               # Shared helper functions
│   │   ├── logger.py        # Day 2: Custom logging utility
│   │   └── helpers.py       # Helper functions
│   ├── validation/          # Pydantic validation schemas
│   │   └── validator.py     # Validator placeholder
│   ├── database/            # Database management and query utilities
│   └── __init__.py          # Package initializer
│
├── tests/                   # Test suite
│   ├── etl/                 # ETL unit/integration tests
│   │   ├── test_loader.py   # Day 2: Loader tests
│   │   └── test_normalizer.py # Day 2: Normalizer tests
│   ├── validation/          # Data validation tests
│   └── database/            # Database connection & query tests
│
├── logs/                    # Runtime logs (app.log)
│
├── .env                     # Local environment configurations
├── .gitignore               # Version control ignore lists
├── Makefile                 # Automation shortcuts
├── README.md                # Project documentation
├── requirements.txt         # Project dependencies
└── main.py                  # Pipeline execution entrypoint
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- SQLite3 (built-in with Python)

### Installation

1. Clone this repository to your local workspace.
2. Initialize environment configurations:
   ```bash
   cp .env.example .env  # or rename .env if present
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   Or using the automation command:
   ```bash
   make install
   ```

### Running the Pipeline

To run the main initialization and start the pipeline:
```bash
python main.py
```
Or:
```bash
make run
```

### Running Tests

Execute the test suite using `pytest`:
```bash
pytest
```
Or:
```bash
make test
```

## 🛠️ Tech Stack & Utilities

- **Language:** Python 3.14+
- **Database:** SQLite
- **Libraries:** Pandas, Openpyxl, Pytest, python-dotenv
