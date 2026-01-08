#!/usr/bin/env python3
"""
Add optimization indexes to speed up get_top_topics query
"""

import psycopg
from dotenv import load_dotenv
import os

load_dotenv()
POSTGRES_DSN = os.getenv("POSTGRES_DSN")

def add_indexes():
    """Add optimization indexes"""
    conn = psycopg.connect(POSTGRES_DSN)
    cur = conn.cursor()
    
    try:
        print("🔄 Adding optimization indexes...")
        
        # Composite index: speed up reviews_topics aggregation queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_topics_airline_sentiment_topic 
            ON reviews_topics("airlineName", sentiment_bucket, topic_id);
        """)
        print("✅ Created index: idx_reviews_topics_airline_sentiment_topic")
        
        # Partial index: only index non-NULL airlineName
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_topics_sentiment_airline_not_null 
            ON topics(sentiment_bucket, "airlineName") 
            WHERE "airlineName" IS NOT NULL;
        """)
        print("✅ Created index: idx_topics_sentiment_airline_not_null")
        
        # Analyze tables to update statistics
        cur.execute("ANALYZE reviews_topics;")
        cur.execute("ANALYZE topics;")
        print("✅ Updated table statistics")
        
        conn.commit()
        print("✅ All indexes created successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    add_indexes()

