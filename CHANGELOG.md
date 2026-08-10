# Changelog

All notable changes to the Nifty 100 Financial Intelligence Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-08-10

This is the production-ready Release 1.0.0 of the Nifty 100 Financial Intelligence Platform, completing all Sprint deliverables and releasing a fully tested, containerized dashboard and REST API suite.

### Added
- **Interactive REST API (Day 39)**: Exposes endpoints for constituents listing, details by ticker, dynamic valuation flag mapping, strategy-based screeners, and sector-relative peer benchmarks. Includes `/docs` Swagger support.
- **Dockerization (Day 37)**: Multi-container setup with health checks, local persistency directory links, and hot-reload.
- **CI/CD Workflow (Day 38)**: GitHub Actions automation checking PEP 8 format, running ETL pipeline databases builds, and executing the 309-test suite on every push or Pull Request.
- **Project Documentation (Day 40)**: Complete system design documentation folder including installations instructions, database schema descriptions, calculations equations, and REST route specifications.
- **Performance Benchmarks (Day 41)**: Systematic latency analysis across all endpoints, bypass guidelines for Windows resolution overheads, and production scale tuning setups (WAL mode, Gunicorn workers).
- **Project Statistics Engine (Day 42)**: Interactive project analyzer printing lines of code counts, files breakdown, test metrics, and database records count.

---

## [0.5.0] - 2026-08-06

### Added
- **Sprint 5 Portfolio Reporting**: Implemented the modular PDF reporting architecture to compile a 92-page executive summary document covering all constituents alphabetically.
- **Capital Allocation Analytics**: Integrated strategy transition rules (e.g. debt-repayment vs dividend distributions) and cash flow metrics.

---

## [0.4.0] - 2026-07-28

### Added
- **Streamlit Frontend Dashboard**: Implemented multi-page application foundation with navigation, KPI components, and custom CSS stylings.
- **Visual Analytics Suite**: Created radar charts, historical trend charts, and sector valuation heatmaps.

---

## [0.3.0] - 2026-07-25

### Added
- **Screener Preset Pipeline**: Implemented 6 predefined screeners (Quality Compounder, Value Pick, Growth Accelerator, Dividend Champion, Debt-Free Blue Chip, and Turnaround Watch).
- **Composite Quality Score (CQS)**: Normalization and winsorization ranking engine.

---

## [0.2.0] - 2026-07-20

### Added
- **Data Quality (DQ) Validator**: Automated parser checking cell formats, schema rules, and flagging anomalies.
- **ETL Loader**: Excel parse rules inserting company profiles, P&L, balance sheets, and cash flows.

---

## [0.1.0] - 2026-07-15

### Added
- Initial project workspace structure, database models, and initial parsing scripts.

[1.0.0]: https://github.com/krishnavasnani07/n100-financial-intelligence-platform/releases/tag/v1.0.0
[0.5.0]: https://github.com/krishnavasnani07/n100-financial-intelligence-platform/releases/tag/v0.5.0
[0.4.0]: https://github.com/krishnavasnani07/n100-financial-intelligence-platform/releases/tag/v0.4.0
[0.3.0]: https://github.com/krishnavasnani07/n100-financial-intelligence-platform/releases/tag/v0.3.0
[0.2.0]: https://github.com/krishnavasnani07/n100-financial-intelligence-platform/releases/tag/v0.2.0
[0.1.0]: https://github.com/krishnavasnani07/n100-financial-intelligence-platform/releases/tag/v0.1.0
