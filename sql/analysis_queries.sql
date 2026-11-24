-- Queries run by notebooks/01_profit_leakage_analysis.ipynb against the cleaned `orders`
-- table (DuckDB, PostgreSQL-compatible syntax). Blocks are loaded by "-- name:".

-- name: kpi_by_year
SELECT
    EXTRACT(year FROM order_date)::INT          AS year,
    COUNT(*)                                    AS order_lines,
    ROUND(SUM(sales))                           AS sales,
    ROUND(SUM(profit))                          AS profit,
    ROUND(100 * SUM(profit) / SUM(sales), 1)    AS margin_pct,
    ROUND(100 * AVG(discount), 2)               AS avg_discount_pct
FROM orders
GROUP BY 1
ORDER BY 1;

-- name: subcategory_profit
SELECT
    category,
    sub_category,
    COUNT(*)                                        AS order_lines,
    ROUND(SUM(sales))                               AS sales,
    ROUND(SUM(profit))                              AS profit,
    ROUND(100 * SUM(profit) / SUM(sales), 1)        AS margin_pct,
    ROUND(100 * AVG(CASE WHEN profit < 0 THEN 1 ELSE 0 END), 1) AS loss_line_pct
FROM orders
GROUP BY 1, 2
ORDER BY profit;

-- name: loss_lines
SELECT
    COUNT(*) FILTER (WHERE profit < 0)                  AS loss_lines,
    ROUND(100.0 * COUNT(*) FILTER (WHERE profit < 0) / COUNT(*), 1) AS loss_line_pct,
    ROUND(SUM(profit) FILTER (WHERE profit < 0))        AS total_losses,
    ROUND(SUM(profit) FILTER (WHERE profit >= 0))       AS total_gains,
    ROUND(SUM(profit))                                  AS net_profit
FROM orders;

-- name: margin_by_discount_band
SELECT
    discount_band,
    COUNT(*)                                    AS order_lines,
    ROUND(SUM(sales))                           AS sales,
    ROUND(100 * SUM(profit) / SUM(sales), 1)    AS margin_pct
FROM orders
GROUP BY 1
ORDER BY 1;

-- name: mix_adjusted_discount_effect
-- Compare margins of high vs low discount lines *within* each sub-category, then weight by sales.
-- This removes the effect of product mix (e.g. Tables are both heavily discounted and low margin).
WITH by_sub AS (
    SELECT
        sub_category,
        SUM(sales)                                                                  AS sub_sales,
        SUM(profit) FILTER (WHERE discount <= 0.05) / SUM(sales) FILTER (WHERE discount <= 0.05) AS margin_low_disc,
        SUM(profit) FILTER (WHERE discount >  0.05) / SUM(sales) FILTER (WHERE discount >  0.05) AS margin_high_disc
    FROM orders
    GROUP BY 1
)
SELECT
    ROUND(100 * SUM(sub_sales * margin_low_disc)  / SUM(sub_sales), 1) AS margin_low_disc_pct,
    ROUND(100 * SUM(sub_sales * margin_high_disc) / SUM(sub_sales), 1) AS margin_high_disc_pct,
    ROUND(100 * SUM(sub_sales * (margin_high_disc - margin_low_disc)) / SUM(sub_sales), 1) AS mix_adjusted_gap_pp,
    COUNT(*) FILTER (WHERE margin_high_disc < margin_low_disc)          AS subcats_where_discount_hurts,
    COUNT(*)                                                            AS subcats
FROM by_sub;

-- name: shipping_by_mode
SELECT
    ship_mode,
    category,
    COUNT(*)                                                    AS order_lines,
    ROUND(SUM(sales))                                           AS sales,
    ROUND(100 * SUM(profit) / SUM(sales), 1)                    AS margin_pct
FROM orders
GROUP BY 1, 2
ORDER BY 1, 2;

-- name: priority_margin
SELECT
    order_priority,
    COUNT(*)                                    AS order_lines,
    ROUND(100 * SUM(profit) / SUM(sales), 1)    AS margin_pct
FROM orders
GROUP BY 1
ORDER BY margin_pct;
