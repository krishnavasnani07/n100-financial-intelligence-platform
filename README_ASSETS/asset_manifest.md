# Visual Asset Manifest

This manifest documents all visual identity assets and diagrams used throughout the N100 Financial Intelligence Platform repository. 

---

## 🎨 Asset Matrix

| Asset File | Format | Purpose / Description | Used In |
| :--- | :---: | :--- | :--- |
| [`banner.png`](file:///c:/Users/Krishna/Documents/n100-financial-intelligence-platform/README_ASSETS/banner.png) | PNG | Sleek, dark-mode hero banner representing project identity and core capabilities. | [`README.md`](file:///c:/Users/Krishna/Documents/n100-financial-intelligence-platform/README.md) (Header) |
| [`social_preview.png`](file:///c:/Users/Krishna/Documents/n100-financial-intelligence-platform/README_ASSETS/social_preview.png) | PNG | Open Graph image optimized for GitHub sharing card previews. | Repository Settings / Social Card |
| [`architecture.svg`](file:///c:/Users/Krishna/Documents/n100-financial-intelligence-platform/README_ASSETS/architecture.svg) | SVG | High-level system overview map mapping Ingestion -> Parsing -> Validation -> Storage -> Calculations -> UI. | [`README.md`](file:///c:/Users/Krishna/Documents/n100-financial-intelligence-platform/README.md), [`docs/architecture.md`](file:///c:/Users/Krishna/Documents/n100-financial-intelligence-platform/docs/architecture.md) |
| [`etl_flow.svg`](file:///c:/Users/Krishna/Documents/n100-financial-intelligence-platform/README_ASSETS/etl_flow.svg) | SVG | Detailed step-by-step lifecycle flow of the transactional ETL and validation stages. | [`README.md`](file:///c:/Users/Krishna/Documents/n100-financial-intelligence-platform/README.md), [`docs/etl_pipeline.md`](file:///c:/Users/Krishna/Documents/n100-financial-intelligence-platform/docs/etl_pipeline.md) |
| [`database_schema.svg`](file:///c:/Users/Krishna/Documents/n100-financial-intelligence-platform/README_ASSETS/database_schema.svg) | SVG | SQLite database relational schema entity-relationship diagram with keys, indexes, and constraints. | [`README.md`](file:///c:/Users/Krishna/Documents/n100-financial-intelligence-platform/README.md), [`docs/database.md`](file:///c:/Users/Krishna/Documents/n100-financial-intelligence-platform/docs/database.md) |
| [`dashboard.png`](file:///c:/Users/Krishna/Documents/n100-financial-intelligence-platform/README_ASSETS/dashboard.png) | PNG | Live UI screenshot of the Streamlit Executive Dashboard displaying real sector and quality distributions. | [`README.md`](file:///c:/Users/Krishna/Documents/n100-financial-intelligence-platform/README.md) |
| [`cli_execution.png`](file:///c:/Users/Krishna/Documents/n100-financial-intelligence-platform/README_ASSETS/cli_execution.png) | PNG | Terminal rendering of the successful ETL pipeline execution stats showing load metrics. | [`README.md`](file:///c:/Users/Krishna/Documents/n100-financial-intelligence-platform/README.md), [`docs/etl_pipeline.md`](file:///c:/Users/Krishna/Documents/n100-financial-intelligence-platform/docs/etl_pipeline.md) |
| [`test_suite.png`](file:///c:/Users/Krishna/Documents/n100-financial-intelligence-platform/README_ASSETS/test_suite.png) | PNG | Terminal rendering of the successful test suite run showing 279 passing green unit/integration tests. | [`README.md`](file:///c:/Users/Krishna/Documents/n100-financial-intelligence-platform/README.md) |
| [`demo_plan.md`](file:///c:/Users/Krishna/Documents/n100-financial-intelligence-platform/README_ASSETS/demo_plan.md) | Markdown | Script for a 90-second recording presentation demo covering core value, architecture, and code. | Repository Presentation Reference |

---

## 🛠️ Maintenance & Regeneration
Vector diagrams (`.svg`) and CLI screenshots are compiled dynamically:
* Diagram shapes and texts can be customized by editing the SVG builder script: `scratch/generate_diagrams.py`.
* Terminal rendering styles (Slate themes, window control frames) can be customized in the rendering script: `scratch/render_terminal.py`.
