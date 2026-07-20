-- ====================================================================
-- CASH FLOW & CAPITAL ALLOCATION EXPLORATORY QUERIES
-- Nifty 100 Financial Intelligence Platform — Sprint 2 Day 11
-- ====================================================================

-- 1. Top 10 Operating Cash Flow (CFO) Generators in Latest Year
SELECT 
    cf.company_id,
    c.company_name,
    cf.year,
    cf.operating_activity AS cfo_in_cr,
    cf.investing_activity AS cfi_in_cr,
    cf.financing_activity AS cff_in_cr
FROM cashflow cf
JOIN companies c ON cf.company_id = c.id
WHERE cf.year = 'Mar 2024'
ORDER BY cf.operating_activity DESC
LIMIT 10;

-- 2. Companies with Persistent Operating Cash Flow Burn (CFO < 0)
SELECT 
    cf.company_id,
    c.company_name,
    COUNT(*) AS negative_cfo_years,
    ROUND(AVG(cf.operating_activity), 2) AS avg_cfo_cr
FROM cashflow cf
JOIN companies c ON cf.company_id = c.id
WHERE cf.operating_activity < 0
GROUP BY cf.company_id, c.company_name
HAVING COUNT(*) >= 2
ORDER BY negative_cfo_years DESC, avg_cfo_cr ASC;

-- 3. High CapEx Spenders (CFI Outflows > Rs. 5000 Cr)
SELECT 
    cf.company_id,
    c.company_name,
    cf.year,
    ABS(cf.investing_activity) AS capex_cr,
    pl.sales,
    ROUND((ABS(cf.investing_activity) / pl.sales) * 100, 2) AS capex_intensity_pct
FROM cashflow cf
JOIN companies c ON cf.company_id = c.id
JOIN profitandloss pl ON cf.company_id = pl.company_id AND cf.year = pl.year
WHERE ABS(cf.investing_activity) > 5000 AND pl.sales > 0
ORDER BY capex_cr DESC;
