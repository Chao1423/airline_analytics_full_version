-- ============================================
-- Create Topic Driver Results table
-- ============================================
-- Used to store OLS regression analysis results, explaining how ratings are driven by topic shares

CREATE TABLE IF NOT EXISTS topic_driver_results (
    id SERIAL PRIMARY KEY,
    "airlineName" TEXT NOT NULL,
    model_spec TEXT NOT NULL DEFAULT 'default',  -- Model specification identifier (can be used for different time ranges, filter conditions, etc.)
    topic_id INTEGER NOT NULL,
    coef NUMERIC(10, 6) NOT NULL,  -- Regression coefficient
    se NUMERIC(10, 6) NOT NULL,  -- Standard error
    pval NUMERIC(10, 6) NOT NULL,  -- p-value
    ci_low NUMERIC(10, 6) NOT NULL,  -- 95% confidence interval lower bound
    ci_high NUMERIC(10, 6) NOT NULL,  -- 95% confidence interval upper bound
    n INTEGER NOT NULL,  -- Sample size
    r2 NUMERIC(5, 4) NOT NULL,  -- R²
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE ("airlineName", model_spec, topic_id, created_at)
);

CREATE INDEX IF NOT EXISTS idx_topic_driver_airline ON topic_driver_results("airlineName");
CREATE INDEX IF NOT EXISTS idx_topic_driver_model_spec ON topic_driver_results(model_spec);
CREATE INDEX IF NOT EXISTS idx_topic_driver_created_at ON topic_driver_results(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_topic_driver_topic ON topic_driver_results(topic_id);

