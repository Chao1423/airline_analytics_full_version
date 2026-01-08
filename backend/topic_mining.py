#!/usr/bin/env python3
"""
Topic Mining: Use BERTopic for topic modeling on positive/negative reviews

Solution: BERTopic
Reasons:
1. Uses semantic embeddings (BERT), captures semantic similarity, better for short texts
2. Automatically optimizes topic count, no manual tuning needed
3. Provides better topic representation and visualization
4. More suitable for short text data like reviews
"""

import psycopg
from dotenv import load_dotenv
import os
from datetime import datetime
from typing import List, Dict, Tuple
import numpy as np
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from umap import UMAP
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer
import warnings
warnings.filterwarnings('ignore')


class TopicMiner:
    """Topic miner"""
    
    def __init__(self, airline_name: str = None, min_topic_size: int = 10, n_topics: int = None, start_date: str = None, end_date: str = None):
        """
        Initialize topic miner
        
        Args:
            airline_name: Airline name (None means all airlines)
            min_topic_size: Minimum topic size (number of reviews)
            n_topics: Number of topics (None means auto-determined)
            start_date: Start date (optional, YYYY-MM-DD)
            end_date: End date (optional, YYYY-MM-DD)
        """
        self.airline_name = airline_name
        self.min_topic_size = min_topic_size
        self.n_topics = n_topics
        self.start_date = start_date
        self.end_date = end_date
        
        # Initialize BERTopic components
        # Use lightweight model for better speed
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # UMAP dimensionality reduction
        self.umap_model = UMAP(
            n_neighbors=15,
            n_components=5,
            min_dist=0.0,
            metric='cosine',
            random_state=42
        )
        
        # HDBSCAN clustering
        self.hdbscan_model = HDBSCAN(
            min_cluster_size=min_topic_size,
            metric='euclidean',
            cluster_selection_method='eom',
            prediction_data=True
        )
        
        # Word vectorization (for topic representation)
        # Dynamically adjust parameters to adapt to different dataset sizes
        self.vectorizer_model = CountVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,  # Lower min_df to adapt to small datasets
            max_df=0.99  # Raise max_df to adapt to small datasets
        )
        
    def prepare_data(self, db_conn, sentiment_bucket: str) -> Tuple[List[str], List[str], List[str], List[datetime]]:
        """
        Prepare data: Get review texts from database
        
        Args:
            db_conn: Database connection
            sentiment_bucket: 'pos' or 'neg'
            
        Returns:
            (review_ids, texts, airline_names, review_months)
        """
        cur = db_conn.cursor()
        
        try:
            # Map sentiment_bucket to actual sentiment_label values
            sentiment_map = {
                'pos': 'Positive',
                'neg': 'Negative'
            }
            actual_sentiment = sentiment_map.get(sentiment_bucket, sentiment_bucket)
            
            # Get cleaned review texts
            query = """
                SELECT 
                    r."reviewId",
                    rc.cleaned_text,
                    r."airlineName",
                    DATE_TRUNC('month', r."dateReview")::DATE as review_month
                FROM reviews r
                INNER JOIN reviews_clean rc ON r."reviewId" = rc.review_id
                INNER JOIN reviews_sentiment rs ON r."reviewId" = rs.review_id
                WHERE rs.sentiment_label = %s
                    AND rc.cleaned_text IS NOT NULL
                    AND rc.cleaned_text != ''
                    AND rc.lang = 'en'
            """
            
            params = [actual_sentiment]
            
            if self.airline_name:
                query += " AND LOWER(r.\"airlineName\") = LOWER(%s)"
                params.append(self.airline_name)
            
            if self.start_date:
                query += " AND r.\"dateReview\" >= %s"
                params.append(self.start_date)
            
            if self.end_date:
                query += " AND r.\"dateReview\" <= %s"
                params.append(self.end_date)
            
            query += " ORDER BY r.\"dateReview\" DESC LIMIT 10000;"
            
            cur.execute(query, params)
            results = cur.fetchall()
            
            review_ids = []
            texts = []
            airline_names = []
            review_months = []
            
            for row in results:
                review_id, text, airline, month = row
                if text and len(text.strip()) > 10:  # Filter too short texts
                    review_ids.append(review_id)
                    texts.append(text)
                    airline_names.append(airline)
                    review_months.append(month)
            
            print(f"📊 Prepared {len(texts)} {sentiment_bucket} reviews for topic modeling")
            return review_ids, texts, airline_names, review_months
            
        except Exception as e:
            print(f"❌ Error preparing data: {e}")
            import traceback
            traceback.print_exc()
            return [], [], [], []
        finally:
            cur.close()
    
    def fit_model(self, texts: List[str]) -> BERTopic:
        """
        Fit BERTopic model
        
        Args:
            texts: List of review texts
            
        Returns:
            BERTopic model
        """
        if len(texts) < self.min_topic_size * 2:
            raise ValueError(f"Insufficient texts: {len(texts)} < {self.min_topic_size * 2}")
        
        # Create BERTopic model
        topic_model = BERTopic(
            embedding_model=self.embedding_model,
            umap_model=self.umap_model,
            hdbscan_model=self.hdbscan_model,
            vectorizer_model=self.vectorizer_model,
            top_n_words=10,
            verbose=True
        )
        
        # Fit model
        print(f"🔄 Fitting BERTopic model on {len(texts)} texts...")
        topics, probs = topic_model.fit_transform(texts)
        
        # If topic count is specified, reduce topics
        if self.n_topics and self.n_topics < len(set(topics)):
            print(f"🔄 Reducing topics to {self.n_topics}...")
            topic_model.reduce_topics(texts, topics, nr_topics=self.n_topics)
            topics, probs = topic_model.transform(texts)
        
        print(f"✅ Model fitted. Found {len(set(topics)) - (1 if -1 in topics else 0)} topics (excluding noise)")
        
        return topic_model
    
    def extract_topics_info(self, topic_model: BERTopic) -> Dict[int, Dict]:
        """
        Extract topic information
        
        Args:
            topic_model: BERTopic model
            
        Returns:
            Topic information dictionary {topic_id: {top_words: [...], human_label: ...}}
        """
        topics_info = {}
        
        # Get topic information
        topic_info = topic_model.get_topic_info()
        
        for idx, row in topic_info.iterrows():
            topic_id = int(row['Topic'])
            if topic_id == -1:  # Skip noise topic
                continue
            
            # Get topic keywords
            topic_words = topic_model.get_topic(topic_id)
            top_words = [word for word, score in topic_words[:10]]
            
            # Generate human label (using first 3 keywords)
            human_label = ' / '.join(top_words[:3])
            
            topics_info[topic_id] = {
                'top_words': top_words,
                'human_label': human_label
            }
        
        return topics_info
    
    def save_to_database(
        self,
        db_conn,
        sentiment_bucket: str,
        review_ids: List[str],
        texts: List[str],
        airline_names: List[str],
        review_months: List[datetime],
        topic_model: BERTopic,
        topics_info: Dict[int, Dict]
    ):
        """
        Save topic mining results to database
        
        Args:
            db_conn: Database connection
            sentiment_bucket: 'pos' or 'neg'
            review_ids: List of review IDs
            texts: List of review texts
            airline_names: List of airline names
            review_months: List of review months
            topic_model: BERTopic model
            topics_info: Topic information dictionary
        """
        cur = db_conn.cursor()
        
        try:
            # Get topic assignments and probabilities
            topics, probs = topic_model.transform(texts)
            
            # Save topic metadata to topics table
            for topic_id, info in topics_info.items():
                # Get main airline for this topic (if airline is specified)
                main_airline = self.airline_name if self.airline_name else None
                
                cur.execute(
                    """
                    INSERT INTO topics (topic_id, sentiment_bucket, "airlineName", top_words, human_label)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (topic_id, sentiment_bucket, COALESCE("airlineName", '')) 
                    DO UPDATE SET
                        top_words = EXCLUDED.top_words,
                        human_label = EXCLUDED.human_label;
                    """,
                    (topic_id, sentiment_bucket, main_airline, info['top_words'], info['human_label'])
                )
            
            # Save review-topic associations to reviews_topics table
            inserted = 0
            for i, (review_id, airline, month) in enumerate(zip(review_ids, airline_names, review_months)):
                topic_id = topics[i]
                topic_score = float(probs[i]) if probs[i] is not None else 0.0
                
                # Skip noise topic (topic_id == -1)
                if topic_id == -1:
                    continue
                
                try:
                    cur.execute(
                        """
                        INSERT INTO reviews_topics (
                            review_id, "airlineName", topic_id, topic_score,
                            sentiment_bucket, review_month
                        )
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (review_id, "airlineName", topic_id, sentiment_bucket)
                        DO UPDATE SET
                            topic_score = EXCLUDED.topic_score,
                            review_month = EXCLUDED.review_month;
                        """,
                        (review_id, airline, topic_id, topic_score, sentiment_bucket, month)
                    )
                    inserted += 1
                except Exception as e:
                    print(f"  ⚠️  Error inserting review {review_id}: {e}")
                    continue
            
            db_conn.commit()
            print(f"✅ Saved {inserted} review-topic associations to database")
            
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
            import traceback
            traceback.print_exc()
            db_conn.rollback()
        finally:
            cur.close()
    
    def mine_topics(self, db_conn, sentiment_bucket: str):
        """
        Execute topic mining workflow
        
        Args:
            db_conn: Database connection
            sentiment_bucket: 'pos' or 'neg'
        """
        print(f"\n{'='*60}")
        print(f"🔍 Mining {sentiment_bucket.upper()} topics for {self.airline_name or 'all airlines'}")
        print(f"{'='*60}\n")
        
        # 1. Prepare data
        review_ids, texts, airline_names, review_months = self.prepare_data(db_conn, sentiment_bucket)
        
        if len(texts) < self.min_topic_size * 2:
            print(f"⚠️  Insufficient data: {len(texts)} texts (need at least {self.min_topic_size * 2})")
            return
        
        # 2. Fit model
        try:
            topic_model = self.fit_model(texts)
        except Exception as e:
            print(f"❌ Error fitting model: {e}")
            return
        
        # 3. Extract topic information
        topics_info = self.extract_topics_info(topic_model)
        
        # 4. Save to database
        self.save_to_database(
            db_conn, sentiment_bucket,
            review_ids, texts, airline_names, review_months,
            topic_model, topics_info
        )
        
        print(f"\n✅ Topic mining completed for {sentiment_bucket.upper()} reviews\n")


def main():
    """Main function"""
    import sys
    
    load_dotenv()
    POSTGRES_DSN = os.getenv("POSTGRES_DSN")
    
    if not POSTGRES_DSN:
        print("❌ POSTGRES_DSN not found in environment")
        return
    
    # Parse arguments
    airline_name = sys.argv[1] if len(sys.argv) > 1 else None
    sentiment = sys.argv[2] if len(sys.argv) > 2 else 'both'  # 'pos', 'neg', or 'both'
    min_topic_size = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    n_topics = int(sys.argv[4]) if len(sys.argv) > 4 else None
    
    conn = psycopg.connect(POSTGRES_DSN)
    
    try:
        miner = TopicMiner(
            airline_name=airline_name,
            min_topic_size=min_topic_size,
            n_topics=n_topics
        )
        
        # Mine topics
        if sentiment in ['pos', 'both']:
            miner.mine_topics(conn, 'pos')
        
        if sentiment in ['neg', 'both']:
            miner.mine_topics(conn, 'neg')
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    main()

