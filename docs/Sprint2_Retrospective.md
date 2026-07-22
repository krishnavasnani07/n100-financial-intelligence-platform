# Sprint 2 Retrospective

## Objective
Implemented the Financial Ratio Engine and completed validation work for the core profitability and leverage metrics.

## KPIs
Implemented 17+ KPIs covering profitability, leverage, efficiency, cash flow quality, and composite scoring.

## Challenges
- Negative equity handling
- Debt-free company edge cases
- Zero-base CAGR behavior
- Financial sector D/E carve-out for leverage warnings

## Validation
- 90 tests passed
- ROE validated against the source workbook
- ROCE validated against the source workbook
- Edge cases logged to output/ratio_edge_cases.log

## Improvements
- Peer comparison workflow
- Composite score refinement
- Screener enhancements for business-rule sanity checks
