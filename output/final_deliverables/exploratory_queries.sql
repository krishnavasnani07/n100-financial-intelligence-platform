-- ============================================================================
-- Nifty 100 Financial Intelligence Platform - Exploratory SQL Queries (Sprint 1 - Day 7)
-- ============================================================================

-- Query 1: Total count of master companies loaded in database
SELECT COUNT(*) AS total_companies FROM companies;

-- Query 2: Distribution of companies across broad sectors
SELECT 
    s.broad_sector, 
    COUNT(c.id) AS company_count
FROM companies c
JOIN sectors s ON c.id = s.company_id
GROUP BY s.broad_sector
ORDER BY company_count DESC;

-- Query 3: Latest financial years available in Profit & Loss table
SELECT 
    year, 
    COUNT(company_id) AS record_count
FROM profitandloss
GROUP BY year
ORDER BY year DESC;

-- Query 4: Top 10 companies by sales revenue (Financial Year: Mar 2023)
SELECT 
    c.id AS company_id, 
    c.company_name, 
    pl.sales, 
    pl.net_profit
FROM profitandloss pl
JOIN companies c ON pl.company_id = c.id
WHERE pl.year = 'Mar 2023'
ORDER BY pl.sales DESC
LIMIT 10;

-- Query 5: Companies with negative net profit in any recorded financial year
SELECT 
    c.id AS company_id, 
    c.company_name, 
    pl.year, 
    pl.net_profit
FROM profitandloss pl
JOIN companies c ON pl.company_id = c.id
WHERE pl.net_profit < 0
ORDER BY pl.net_profit ASC;

-- Query 6: Companies missing annual report documents
SELECT 
    c.id AS company_id, 
    c.company_name
FROM companies c
LEFT JOIN documents d ON c.id = d.company_id
WHERE d.company_id IS NULL;

-- Query 7: Average borrowings/debt by industry sector (Financial Year: Mar 2023)
SELECT 
    s.broad_sector, 
    ROUND(AVG(bs.borrowings), 2) AS avg_borrowings,
    ROUND(MAX(bs.borrowings), 2) AS max_borrowings
FROM balancesheet bs
JOIN sectors s ON bs.company_id = s.company_id
WHERE bs.year = 'Mar 2023'
GROUP BY s.broad_sector
ORDER BY avg_borrowings DESC;

-- Query 8: Top 10 companies by Total Assets (Financial Year: Mar 2023)
SELECT 
    c.id AS company_id, 
    c.company_name, 
    bs.total_assets, 
    bs.equity_capital
FROM balancesheet bs
JOIN companies c ON bs.company_id = c.id
WHERE bs.year = 'Mar 2023'
ORDER BY bs.total_assets DESC
LIMIT 10;

-- Query 9: Cash flow activity summary aggregated across all companies
SELECT 
    cf.year, 
    ROUND(SUM(cf.operating_activity), 2) AS total_operating_cashflow,
    ROUND(SUM(cf.investing_activity), 2) AS total_investing_cashflow,
    ROUND(SUM(cf.financing_activity), 2) AS total_financing_cashflow,
    ROUND(SUM(cf.net_cash_flow), 2) AS total_net_cashflow
FROM cashflow cf
GROUP BY cf.year
ORDER BY cf.year DESC;

-- Query 10: Historical financial year coverage per company
SELECT 
    c.id AS company_id, 
    c.company_name, 
    COUNT(DISTINCT pl.year) AS historical_years_count,
    MIN(pl.year) AS earlist_year,
    MAX(pl.year) AS latest_year
FROM companies c
LEFT JOIN profitandloss pl ON c.id = pl.company_id
GROUP BY c.id, c.company_name
ORDER BY historical_years_count ASC, c.id ASC;
