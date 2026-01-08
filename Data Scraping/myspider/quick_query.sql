-- Quick query SQL script
-- Usage: psql -U chao -d airline_db -f quick_query.sql

-- 1. View all tables and their record counts
SELECT 
    'airlines' as table_name,
    COUNT(*) as record_count
FROM airlines
UNION ALL
SELECT 
    'reviews' as table_name,
    COUNT(*) as record_count
FROM reviews
UNION ALL
SELECT 
    'sentiment' as table_name,
    COUNT(*) as record_count
FROM sentiment;

-- 2. View airline list (Top 20)
SELECT 
    name,
    "reviewCount",
    score,
    "calculatedReviewCount"
FROM airlines
ORDER BY "reviewCount" DESC NULLS LAST
LIMIT 20;

-- 3. View review statistics
SELECT 
    COUNT(*) as total_reviews,
    COUNT(DISTINCT "airlineName") as total_airlines,
    ROUND(AVG(score), 2) as avg_score,
    MIN("dateReview") as earliest_review,
    MAX("dateReview") as latest_review
FROM reviews;

-- 4. Review count ranking by airline
SELECT 
    "airlineName",
    COUNT(*) as review_count,
    ROUND(AVG(score), 2) as avg_score
FROM reviews
GROUP BY "airlineName"
ORDER BY review_count DESC
LIMIT 10;

-- 5. View recent reviews
SELECT 
    "airlineName",
    title,
    score,
    "dateReview",
    LEFT(content, 100) as content_preview
FROM reviews
WHERE "dateReview" IS NOT NULL
ORDER BY "dateReview" DESC
LIMIT 10;

-- 6. View table structure
SELECT 
    table_name,
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
    AND table_name IN ('airlines', 'reviews', 'sentiment')
ORDER BY table_name, ordinal_position;

