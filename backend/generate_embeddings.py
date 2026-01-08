#!/usr/bin/env python3
"""
Generate embeddings for reviews and store in database
"""

import os
import psycopg
from dotenv import load_dotenv
from rag_service import RAGService
from tqdm import tqdm

load_dotenv()
POSTGRES_DSN = os.getenv("POSTGRES_DSN")


def generate_embeddings_for_airline(airline_name: str = None, batch_size: int = 100):
    """
    Generate embeddings for reviews
    
    Args:
        airline_name: Airline name (None means all airlines)
        batch_size: Batch size
    """
    conn = psycopg.connect(POSTGRES_DSN)
    cur = conn.cursor()
    
    try:
        # Initialize RAG service
        service = RAGService(POSTGRES_DSN)
        
        # Query reviews that need embeddings
        where_clause = """
            r."reviewId" NOT IN (
                SELECT review_id FROM review_embeddings 
                WHERE "airlineName" = r."airlineName"
            )
        """
        params = []
        
        if airline_name:
            where_clause += " AND LOWER(r.\"airlineName\") = LOWER(%s)"
            params.append(airline_name)
        
        # Get total review count
        cur.execute(f"""
            SELECT COUNT(*)
            FROM reviews r
            WHERE {where_clause}
        """, tuple(params))
        total_count = cur.fetchone()[0]
        
        if total_count == 0:
            print(f"✅ All reviews already have embeddings for {airline_name or 'all airlines'}")
            return
        
        print(f"🔄 Generating embeddings for {total_count} reviews...")
        
        # Process in batches
        offset = 0
        processed = 0
        
        with tqdm(total=total_count, desc="Processing reviews") as pbar:
            while True:
                cur.execute(f"""
                    SELECT 
                        r."reviewId",
                        r."airlineName",
                        r.title,
                        r.content
                    FROM reviews r
                    WHERE {where_clause}
                    ORDER BY r."dateReview" DESC
                    LIMIT %s OFFSET %s
                """, tuple(params) + (batch_size, offset))
                
                reviews = cur.fetchall()
                
                if not reviews:
                    break
                
                # Generate embeddings in batch
                for review_id, airline, title, content in reviews:
                    try:
                        # Combine text (title + content)
                        text_content = f"{title or ''} {content or ''}".strip()
                        
                        if not text_content:
                            continue
                        
                        # Generate embedding
                        embedding = service.generate_embedding(text_content)
                        
                        # Check if using vectors
                        cur.execute("""
                            SELECT EXISTS (
                                SELECT 1 FROM information_schema.columns 
                                WHERE table_name = 'review_embeddings' 
                                AND column_name = 'embedding'
                            );
                        """)
                        has_vector = cur.fetchone()[0]
                        
                        # Insert or update
                        if has_vector:
                            # Convert to PostgreSQL array format
                            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                            
                            cur.execute("""
                                INSERT INTO review_embeddings (
                                    review_id, "airlineName", embedding, text_content
                                ) VALUES (%s, %s, %s::vector, %s)
                                ON CONFLICT (review_id, "airlineName") 
                                DO UPDATE SET
                                    embedding = EXCLUDED.embedding,
                                    text_content = EXCLUDED.text_content,
                                    updated_at = CURRENT_TIMESTAMP;
                            """, (review_id, airline, embedding_str, text_content))
                        else:
                            # Don't use vectors, only store text
                            cur.execute("""
                                INSERT INTO review_embeddings (
                                    review_id, "airlineName", text_content
                                ) VALUES (%s, %s, %s)
                                ON CONFLICT (review_id, "airlineName") 
                                DO UPDATE SET
                                    text_content = EXCLUDED.text_content,
                                    updated_at = CURRENT_TIMESTAMP;
                            """, (review_id, airline, text_content))
                        
                        processed += 1
                        pbar.update(1)
                        
                    except Exception as e:
                        print(f"\n⚠️  Error processing review {review_id}: {e}")
                        continue
                
                # Commit batch
                conn.commit()
                offset += batch_size
                
                if len(reviews) < batch_size:
                    break
        
        print(f"\n✅ Generated embeddings for {processed} reviews")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    import sys
    
    airline_name = sys.argv[1] if len(sys.argv) > 1 else None
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    
    generate_embeddings_for_airline(airline_name, batch_size)

