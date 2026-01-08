-- ============================================
-- Create sentiment analysis related tables
-- ============================================

-- Create reviews_clean table (cleaned review text)
CREATE TABLE IF NOT EXISTS reviews_clean (
    review_id TEXT NOT NULL,
    "airlineName" TEXT NOT NULL,
    cleaned_text TEXT NOT NULL,
    lang TEXT,
    review_month DATE,
    tokens_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (review_id, "airlineName")
);

-- Create reviews_sentiment table (sentiment analysis results)
CREATE TABLE IF NOT EXISTS reviews_sentiment (
    review_id TEXT NOT NULL,
    "airlineName" TEXT NOT NULL,
    sentiment_label TEXT NOT NULL,  -- 'Positive', 'Neutral', 'Negative'
    sentiment_score NUMERIC(5, 4),  -- -1.0 to 1.0
    model_name TEXT DEFAULT 'cardiffnlp/twitter-roberta-base-sentiment-latest',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (review_id, "airlineName")
);

-- Create indexes to improve query performance
CREATE INDEX IF NOT EXISTS idx_reviews_clean_airline_month 
ON reviews_clean("airlineName", review_month);

CREATE INDEX IF NOT EXISTS idx_reviews_clean_review_id 
ON reviews_clean(review_id, "airlineName");

CREATE INDEX IF NOT EXISTS idx_reviews_sentiment_airline 
ON reviews_sentiment("airlineName");

CREATE INDEX IF NOT EXISTS idx_reviews_sentiment_review_id 
ON reviews_sentiment(review_id, "airlineName");

CREATE INDEX IF NOT EXISTS idx_reviews_sentiment_label 
ON reviews_sentiment(sentiment_label);

-- Create trigger function to update updated_at (if not exists)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for reviews_clean table
DROP TRIGGER IF EXISTS update_reviews_clean_updated_at ON reviews_clean;
CREATE TRIGGER update_reviews_clean_updated_at 
BEFORE UPDATE ON reviews_clean
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create trigger for reviews_sentiment table
DROP TRIGGER IF EXISTS update_reviews_sentiment_updated_at ON reviews_sentiment;
CREATE TRIGGER update_reviews_sentiment_updated_at 
BEFORE UPDATE ON reviews_sentiment
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Display success message
DO $$
BEGIN
    RAISE NOTICE 'Sentiment analysis tables created successfully!';
    RAISE NOTICE 'Tables: reviews_clean, reviews_sentiment';
END $$;

