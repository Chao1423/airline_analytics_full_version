#!/usr/bin/env python3
"""
Create sentiment analysis related tables
"""

import psycopg
from dotenv import load_dotenv
import os

load_dotenv()
POSTGRES_DSN = os.getenv("POSTGRES_DSN")

def create_tables():
    """Create reviews_clean and reviews_sentiment tables"""
    conn = psycopg.connect(POSTGRES_DSN)
    cur = conn.cursor()
    
    try:
        print("🔄 Creating sentiment analysis tables...")
        
        # Create reviews_clean table
        cur.execute("""
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
        """)
        
        # Create reviews_sentiment table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reviews_sentiment (
                review_id TEXT NOT NULL,
                "airlineName" TEXT NOT NULL,
                sentiment_label TEXT NOT NULL,
                sentiment_score NUMERIC(5, 4),
                model_name TEXT DEFAULT 'cardiffnlp/twitter-roberta-base-sentiment-latest',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (review_id, "airlineName")
            );
        """)
        
        # Create indexes
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_clean_airline_month 
            ON reviews_clean("airlineName", review_month);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_clean_review_id 
            ON reviews_clean(review_id, "airlineName");
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_sentiment_airline 
            ON reviews_sentiment("airlineName");
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_sentiment_review_id 
            ON reviews_sentiment(review_id, "airlineName");
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_sentiment_label 
            ON reviews_sentiment(sentiment_label);
        """)
        
        # Create trigger function (if not exists)
        cur.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)
        
        # Create triggers
        cur.execute("""
            DROP TRIGGER IF EXISTS update_reviews_clean_updated_at ON reviews_clean;
            CREATE TRIGGER update_reviews_clean_updated_at 
            BEFORE UPDATE ON reviews_clean
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)
        
        cur.execute("""
            DROP TRIGGER IF EXISTS update_reviews_sentiment_updated_at ON reviews_sentiment;
            CREATE TRIGGER update_reviews_sentiment_updated_at 
            BEFORE UPDATE ON reviews_sentiment
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)
        
        conn.commit()
        
        # Verify tables were created successfully
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('reviews_clean', 'reviews_sentiment');
        """)
        tables = cur.fetchall()
        
        print(f"✅ Tables created successfully!")
        print(f"   Created tables: {[t[0] for t in tables]}")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    create_tables()

