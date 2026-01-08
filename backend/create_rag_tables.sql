-- ============================================
-- Create RAG related tables
-- ============================================

-- Option 1: Use pgvector (recommended, requires pgvector extension)
-- If using pgvector, need to install extension first:
-- CREATE EXTENSION IF NOT EXISTS vector;

-- Create review_embeddings table (store review vector embeddings)
CREATE TABLE IF NOT EXISTS review_embeddings (
    review_id TEXT NOT NULL,
    "airlineName" TEXT NOT NULL,
    embedding vector(384),  -- all-MiniLM-L6-v2 is 384-dimensional
    text_content TEXT NOT NULL,  -- Store text used to generate embedding (title + content)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (review_id, "airlineName"),
    FOREIGN KEY (review_id, "airlineName") REFERENCES reviews ("reviewId", "airlineName") ON DELETE CASCADE
);

-- Create vector index (use HNSW index to improve retrieval speed)
-- CREATE INDEX IF NOT EXISTS idx_review_embeddings_vector 
-- ON review_embeddings USING hnsw (embedding vector_cosine_ops);

-- If pgvector is not available, use GIN index for full-text search
CREATE INDEX IF NOT EXISTS idx_review_embeddings_text 
ON review_embeddings USING gin(to_tsvector('english', text_content));

-- Create other indexes
CREATE INDEX IF NOT EXISTS idx_review_embeddings_airline 
ON review_embeddings("airlineName");

CREATE INDEX IF NOT EXISTS idx_review_embeddings_review_id 
ON review_embeddings(review_id, "airlineName");

-- Create trigger to update updated_at
DROP TRIGGER IF EXISTS update_review_embeddings_updated_at ON review_embeddings;
CREATE TRIGGER update_review_embeddings_updated_at 
BEFORE UPDATE ON review_embeddings
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

