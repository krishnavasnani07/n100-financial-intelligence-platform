-- Nifty 100 Financial Intelligence Platform
-- Day 4 Database Verification Script

-- 1. Check foreign key integrity (Expected: 0 rows returned)
PRAGMA foreign_key_check;

-- 2. Verify row counts across all loaded tables
SELECT 'companies' AS table_name, COUNT(*) AS row_count FROM companies
UNION ALL
SELECT 'sectors', COUNT(*) FROM sectors
UNION ALL
SELECT 'analysis', COUNT(*) FROM analysis
UNION ALL
SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL
SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL
SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL
SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL
SELECT 'documents', COUNT(*) FROM documents
UNION ALL
SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL
SELECT 'peer_groups', COUNT(*) FROM peer_groups
UNION ALL
SELECT 'financial_ratios', COUNT(*) FROM financial_ratios;

-- 3. Verify key sample relations (Join Companies with Sectors & Financial Statements)
SELECT 
    c.id AS company_id,
    c.company_name,
    s.broad_sector,
    COUNT(pl.year) AS years_of_pl_data
FROM companies c
LEFT JOIN sectors s ON c.id = s.company_id
LEFT JOIN profitandloss pl ON c.id = pl.company_id
GROUP BY c.id, c.company_name, s.broad_sector
LIMIT 10;
