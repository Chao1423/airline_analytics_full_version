#!/usr/bin/env python3
"""
Create RAG related tables (fixed version - properly handle transaction rollback)
"""

import psycopg
from dotenv import load_dotenv
import os

load_dotenv()
POSTGRES_DSN = os.getenv("POSTGRES_DSN")

def create_tables():
    """Create review_embeddings table"""
    conn = psycopg.connect(POSTGRES_DSN)
    cur = conn.cursor()
    
    try:
        print("🔄 Creating RAG tables...")
        
        # Check if pgvector extension is installed
        use_vector = False
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()  # Commit extension creation (if successful)
            print("✅ pgvector extension enabled")
            use_vector = True
        except Exception as e:
            conn.rollback()  # Rollback failed transaction
            print(f"⚠️  pgvector extension not available: {e}")
            print("   Will use text-based search instead")
            use_vector = False
        
        # Create review_embeddings table
        if use_vector:
            # Use 384 dimensions (matches all-MiniLM-L6-v2)
            try:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS review_embeddings (
                        review_id TEXT NOT NULL,
                        "airlineName" TEXT NOT NULL,
                        embedding vector(384),
                        text_content TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (review_id, "airlineName"),
                        FOREIGN KEY (review_id, "airlineName") REFERENCES reviews ("reviewId", "airlineName") ON DELETE CASCADE
                    );
                """)
                
                # Create vector index (HNSW)
                try:
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_review_embeddings_vector 
                        ON review_embeddings USING hnsw (embedding vector_cosine_ops);
                    """)
                    print("✅ Vector index created")
                except Exception as e:
                    print(f"⚠️  Could not create vector index: {e}")
                    conn.rollback()
            except Exception as e:
                print(f"⚠️  Could not create table with vector column: {e}")
                conn.rollback()
                use_vector = False  # Fallback to text mode
        
        if not use_vector:
            # Don't use vectors, only store text
            cur.execute("""
                CREATE TABLE IF NOT EXISTS review_embeddings (
                    review_id TEXT NOT NULL,
                    "airlineName" TEXT NOT NULL,
                    text_content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (review_id, "airlineName"),
                    FOREIGN KEY (review_id, "airlineName") REFERENCES reviews ("reviewId", "airlineName") ON DELETE CASCADE
                );
            """)
        
        # Create text index (for BM25 or full-text search)
        try:
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_review_embeddings_text 
                ON review_embeddings USING gin(to_tsvector('english', text_content));
            """)
        except Exception as e:
            print(f"⚠️  Could not create GIN text index: {e}")
            # Try creating simple B-tree index as fallback
            try:
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_review_embeddings_text_btree 
                    ON review_embeddings(text_content);
                """)
                print("✅ Created B-tree text index instead")
            except Exception as e2:
                print(f"⚠️  Could not create text index: {e2}")
                conn.rollback()
        
        # Create other indexes
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_review_embeddings_airline 
            ON review_embeddings("airlineName");
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_review_embeddings_review_id 
            ON review_embeddings(review_id, "airlineName");
        """)
        
        # Create trigger function to update updated_at (if not exists)
        cur.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)
        
        # Create trigger
        cur.execute("""
            DROP TRIGGER IF EXISTS update_review_embeddings_updated_at ON review_embeddings;
            CREATE TRIGGER update_review_embeddings_updated_at 
            BEFORE UPDATE ON review_embeddings
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)
        
        conn.commit()
        print("✅ RAG tables created successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    create_tables()

