#!/usr/bin/env python3
"""
Create/update topic mining related tables
"""

import psycopg
from dotenv import load_dotenv
import os

load_dotenv()
POSTGRES_DSN = os.getenv("POSTGRES_DSN")

def create_tables():
    """Create/update reviews_topics and topics tables"""
    conn = psycopg.connect(POSTGRES_DSN)
    cur = conn.cursor()
    
    try:
        print("🔄 Creating/updating topic mining tables...")
        
        # Drop old tables (if exists and needs to be recreated)
        # Note: This will delete all data, use with caution
        # cur.execute("DROP TABLE IF EXISTS reviews_topics CASCADE;")
        # cur.execute("DROP TABLE IF EXISTS topics CASCADE;")
        
        # Create reviews_topics table (updated version)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS reviews_topics (
                review_id TEXT NOT NULL,
                "airlineName" TEXT NOT NULL,
                topic_id INTEGER NOT NULL,
                topic_score NUMERIC(5, 4) NOT NULL,
                sentiment_bucket TEXT NOT NULL,
                review_month DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (review_id, "airlineName", topic_id, sentiment_bucket)
            );
        """)
        
        # Create topics table
        # Note: PostgreSQL doesn't support functions in PRIMARY KEY, so use UNIQUE constraint
        cur.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                topic_id INTEGER NOT NULL,
                sentiment_bucket TEXT NOT NULL,
                "airlineName" TEXT DEFAULT NULL,
                top_words TEXT[],
                human_label TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (topic_id, sentiment_bucket, "airlineName")
            );
        """)
        
        # Create primary key (use expression index as unique constraint)
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_topics_unique 
            ON topics(topic_id, sentiment_bucket, COALESCE("airlineName", ''));
        """)
        
        # Create indexes
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_topics_review_id 
            ON reviews_topics(review_id, "airlineName");
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_topics_topic_id 
            ON reviews_topics(topic_id);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_topics_sentiment 
            ON reviews_topics(sentiment_bucket);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_topics_airline_sentiment 
            ON reviews_topics("airlineName", sentiment_bucket);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_topics_month 
            ON reviews_topics(review_month);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_topics_sentiment 
            ON topics(sentiment_bucket);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_topics_airline_sentiment 
            ON topics("airlineName", sentiment_bucket);
        """)
        
        # Keep topic_importance table (for OLS regression analysis)
        cur.execute("""
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
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_topic_importance_airline 
            ON topic_importance("airlineName");
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_topic_importance_created_at 
            ON topic_importance(created_at DESC);
        """)
        
        conn.commit()
        
        # Verify tables were created successfully
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('reviews_topics', 'topics', 'topic_importance');
        """)
        tables = cur.fetchall()
        
        print(f"✅ Tables created/updated successfully!")
        print(f"   Available tables: {[t[0] for t in tables]}")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    create_tables()

