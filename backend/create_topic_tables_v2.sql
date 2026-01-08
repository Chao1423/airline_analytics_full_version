-- Update reviews_topics table structure (add sentiment_bucket, airline, month)
-- If table already exists, need to drop or migrate data first

-- Drop old table (if exists and needs to be recreated)
-- DROP TABLE IF EXISTS reviews_topics CASCADE;

-- Create reviews_topics table
CREATE TABLE IF NOT EXISTS reviews_topics (
    review_id TEXT NOT NULL,
    "airlineName" TEXT NOT NULL,
    topic_id INTEGER NOT NULL,
    topic_score NUMERIC(5, 4) NOT NULL,  -- topic_share/score (0.0 to 1.0)
    sentiment_bucket TEXT NOT NULL,  -- 'pos' or 'neg'
    review_month DATE,  -- Review month
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (review_id, "airlineName", topic_id, sentiment_bucket),
    FOREIGN KEY (review_id, "airlineName") REFERENCES reviews ("reviewId", "airlineName") ON DELETE CASCADE
);

-- Create topics table (store topic metadata)
CREATE TABLE IF NOT EXISTS topics (
    topic_id INTEGER NOT NULL,
    sentiment_bucket TEXT NOT NULL,  -- 'pos' or 'neg'
    "airlineName" TEXT DEFAULT NULL,  -- Can be NULL (global topic) or specific airline
    top_words TEXT[],  -- Topic keywords array
    human_label TEXT,  -- Human-labeled topic tag
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (topic_id, sentiment_bucket, "airlineName")
);

-- Create unique index (handle NULL values)
CREATE UNIQUE INDEX IF NOT EXISTS idx_topics_unique 
ON topics(topic_id, sentiment_bucket, COALESCE("airlineName", ''));

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_reviews_topics_review_id ON reviews_topics(review_id, "airlineName");
CREATE INDEX IF NOT EXISTS idx_reviews_topics_topic_id ON reviews_topics(topic_id);
CREATE INDEX IF NOT EXISTS idx_reviews_topics_sentiment ON reviews_topics(sentiment_bucket);
CREATE INDEX IF NOT EXISTS idx_reviews_topics_airline_sentiment ON reviews_topics("airlineName", sentiment_bucket);
CREATE INDEX IF NOT EXISTS idx_reviews_topics_month ON reviews_topics(review_month);
CREATE INDEX IF NOT EXISTS idx_topics_sentiment ON topics(sentiment_bucket);
CREATE INDEX IF NOT EXISTS idx_topics_airline_sentiment ON topics("airlineName", sentiment_bucket);

-- Keep topic_importance table (for OLS regression analysis)
CREATE TABLE IF NOT EXISTS topic_importance (
    id SERIAL PRIMARY KEY,
    "airlineName" TEXT NOT NULL,
    topic_id INTEGER NOT NULL,
    topic_label TEXT,
    coef NUMERIC(10, 6),
    std_err NUMERIC(10, 6),
    p_value NUMERIC(10, 6),
    ci_low NUMERIC(10, 6),
    ci_high NUMERIC(10, 6),
    mean_topic_share NUMERIC(5, 4),
    model_r_squared NUMERIC(5, 4),
    sample_size INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE ("airlineName", topic_id, created_at)
);

CREATE INDEX IF NOT EXISTS idx_topic_importance_airline ON topic_importance("airlineName");
CREATE INDEX IF NOT EXISTS idx_topic_importance_created_at ON topic_importance(created_at DESC);

