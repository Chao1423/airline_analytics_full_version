-- Add optimization indexes to speed up get_top_topics query

-- Composite index: speed up reviews_topics aggregation queries
CREATE INDEX IF NOT EXISTS idx_reviews_topics_airline_sentiment_topic 
ON reviews_topics("airlineName", sentiment_bucket, topic_id);

-- Composite index: speed up topics table queries
CREATE INDEX IF NOT EXISTS idx_topics_sentiment_airline 
ON topics(sentiment_bucket, "airlineName") 
WHERE "airlineName" IS NOT NULL;

-- Partial index: only index non-NULL airlineName (smaller and faster)
CREATE INDEX IF NOT EXISTS idx_topics_sentiment_airline_not_null 
ON topics(sentiment_bucket, "airlineName") 
WHERE "airlineName" IS NOT NULL;

-- For case-insensitive compatibility, can consider using function index (but PostgreSQL requires lower() function index)
-- CREATE INDEX IF NOT EXISTS idx_reviews_topics_airline_lower 
-- ON reviews_topics(LOWER("airlineName"), sentiment_bucket, topic_id);

-- Analyze tables to update statistics
ANALYZE reviews_topics;
ANALYZE topics;

