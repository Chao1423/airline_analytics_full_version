-- ============================================
-- Create monthly trends materialized view
-- ============================================
-- This materialized view can significantly improve query performance, especially for large historical data

-- Drop existing materialized view (if exists)
DROP MATERIALIZED VIEW IF EXISTS monthly_trends_mv;

-- Create materialized view
CREATE MATERIALIZED VIEW monthly_trends_mv AS
WITH monthly_stats AS (
    SELECT 
        "airlineName",
        DATE_TRUNC('month', "dateReview") as month,
        COUNT(*) as review_count,
        AVG(score) as avg_rating
    FROM reviews
    WHERE score IS NOT NULL 
        AND "dateReview" IS NOT NULL
        AND "dateReview" >= '2020-01-01'
    GROUP BY "airlineName", DATE_TRUNC('month', "dateReview")
),
monthly_destinations AS (
    SELECT 
        "airlineName",
        DATE_TRUNC('month', "dateReview") as month,
        route,
        COUNT(*) as route_count
    FROM reviews
    WHERE route IS NOT NULL
        AND route != ''
        AND "dateReview" IS NOT NULL
        AND "dateReview" >= '2020-01-01'
    GROUP BY "airlineName", DATE_TRUNC('month', "dateReview"), route
),
top_destinations_by_month AS (
    SELECT 
        "airlineName",
        month,
        route,
        route_count,
        ROW_NUMBER() OVER (PARTITION BY "airlineName", month ORDER BY route_count DESC) as rn
    FROM monthly_destinations
)
SELECT 
    ms."airlineName",
    TO_CHAR(ms.month, 'YYYY-MM') as month,
    ms.review_count,
    ROUND(ms.avg_rating::numeric, 2) as avg_rating,
    NULL::numeric as sentiment_mean,  -- Placeholder for future sentiment analysis
    COALESCE(
        json_agg(
            json_build_object('destination', td.route, 'count', td.route_count)
            ORDER BY td.route_count DESC
        ) FILTER (WHERE td.rn <= 5),
        '[]'::json
    ) as destination_topN
FROM monthly_stats ms
LEFT JOIN top_destinations_by_month td 
    ON ms."airlineName" = td."airlineName" 
    AND ms.month = td.month 
    AND td.rn <= 5
GROUP BY ms."airlineName", ms.month, ms.review_count, ms.avg_rating;

-- Create indexes to improve query performance
CREATE INDEX IF NOT EXISTS idx_monthly_trends_mv_airline_month 
ON monthly_trends_mv("airlineName", month);

-- Create unique index
CREATE UNIQUE INDEX IF NOT EXISTS idx_monthly_trends_mv_unique 
ON monthly_trends_mv("airlineName", month);

-- Display success message
DO $$
BEGIN
    RAISE NOTICE 'Monthly trends materialized view created successfully!';
END $$;

