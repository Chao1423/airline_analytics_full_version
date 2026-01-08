#!/usr/bin/env python3
"""
RAG Service - Answer questions using vector retrieval and DeepSeek API
"""

import os
import json
import requests
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
import psycopg
import numpy as np
from sentence_transformers import SentenceTransformer

load_dotenv()

# DeepSeek API configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# Use sentence-transformers to generate embeddings (local model, no API needed)
# Use all-MiniLM-L6-v2 (384 dim) or all-mpnet-base-v2 (768 dim)
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # Lightweight, fast
EMBEDDING_DIM = 384


class RAGService:
    """RAG service class"""
    
    def __init__(self, db_dsn: str):
        self.db_dsn = db_dsn
        self.embedding_model = None
        self._load_embedding_model()
    
    def _load_embedding_model(self):
        """Load embedding model"""
        try:
            print(f"🔄 Loading embedding model: {EMBEDDING_MODEL_NAME}...")
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
            print("✅ Embedding model loaded")
        except Exception as e:
            print(f"❌ Error loading embedding model: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if not self.embedding_model:
            raise ValueError("Embedding model not loaded")
        
        embedding = self.embedding_model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    
    def retrieve_reviews(
        self,
        query: str,
        airline_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        destination: Optional[str] = None,
        sentiment: Optional[str] = None,  # 'pos', 'neg', 'neutral'
        top_k: int = 10
    ) -> List[Dict]:
        """
        Retrieve relevant reviews
        
        Args:
            query: User query
            airline_name: Airline name
            start_date: Start date
            end_date: End date
            destination: Destination keyword
            sentiment: Sentiment tendency
            top_k: Return top K reviews
            
        Returns:
            List of relevant reviews, containing review_id, content, score, dateReview, etc.
        """
        conn = psycopg.connect(self.db_dsn)
        cur = conn.cursor()
        
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Build WHERE conditions
            where_conditions = ['LOWER(r."airlineName") = LOWER(%s)']
            params = [airline_name]
            
            if start_date:
                where_conditions.append('r."dateReview" >= %s')
                params.append(start_date)
            if end_date:
                where_conditions.append('r."dateReview" <= %s')
                params.append(end_date)
            if destination:
                where_conditions.append('LOWER(r.route) LIKE LOWER(%s)')
                params.append(f'%{destination}%')
            if sentiment:
                # Map sentiment to database values
                sentiment_map = {
                    'pos': 'Positive',
                    'neg': 'Negative',
                    'neutral': 'Neutral'
                }
                actual_sentiment = sentiment_map.get(sentiment.lower(), sentiment)
                where_conditions.append('rs.sentiment_label = %s')
                params.append(actual_sentiment)
            
            where_clause = ' AND '.join(where_conditions)
            
            # Check if vector retrieval is available
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'review_embeddings' 
                    AND column_name = 'embedding'
                );
            """)
            has_vector = cur.fetchone()[0]
            
            if has_vector:
                # Use vector retrieval (pgvector)
                # Convert embedding to PostgreSQL array format
                embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
                
                query_sql = f"""
                    SELECT 
                        r."reviewId",
                        r.title,
                        r.content,
                        r.score,
                        r."dateReview",
                        r.route,
                        rs.sentiment_label,
                        re.text_content,
                        1 - (re.embedding <=> %s::vector) as similarity
                    FROM reviews r
                    LEFT JOIN reviews_sentiment rs ON r."reviewId" = rs.review_id 
                        AND LOWER(r."airlineName") = LOWER(rs."airlineName")
                    LEFT JOIN review_embeddings re ON r."reviewId" = re.review_id 
                        AND LOWER(r."airlineName") = LOWER(re."airlineName")
                    WHERE {where_clause}
                        AND re.embedding IS NOT NULL
                    ORDER BY re.embedding <=> %s::vector
                    LIMIT %s;
                """
                cur.execute(query_sql, tuple(params) + (embedding_str, embedding_str, top_k))
            else:
                # Use text similarity (BM25 or keyword matching)
                # Extract query keywords
                query_keywords = query.lower().split()
                
                # Build keyword LIKE conditions (use OR to connect multiple LIKE)
                keyword_conditions = []
                keyword_params = []
                for kw in query_keywords:
                    keyword_conditions.append('LOWER(COALESCE(re.text_content, r.title || \' \' || r.content)) LIKE %s')
                    keyword_params.append(f'%{kw}%')
                
                keyword_like_clause = ' OR '.join(keyword_conditions) if keyword_conditions else '1=0'
                
                # If only WHERE conditions without other filters, ensure at least review_embeddings data exists
                # Check if review_embeddings join condition exists
                has_review_embeddings_check = True
                
                # Simplify similarity calculation, avoid reusing keyword_like_clause
                # Simplify query: use LIKE matching first, then sort by relevance
                # If full-text search has no results, use LIKE matching
                # Simplify query: temporarily don't use ts_rank in SELECT, avoid parameter issues
                # First ensure results can be retrieved, use fixed value for similarity
                query_sql = f"""
                    SELECT 
                        r."reviewId",
                        r.title,
                        r.content,
                        r.score,
                        r."dateReview",
                        r.route,
                        rs.sentiment_label,
                        COALESCE(re.text_content, r.title || ' ' || r.content) as text_content,
                        0.1 as similarity
                    FROM reviews r
                    LEFT JOIN reviews_sentiment rs ON r."reviewId" = rs.review_id 
                        AND LOWER(r."airlineName") = LOWER(rs."airlineName")
                    INNER JOIN review_embeddings re ON r."reviewId" = re.review_id 
                        AND LOWER(r."airlineName") = LOWER(re."airlineName")
                    WHERE {where_clause}
                        AND (
                            to_tsvector('english', COALESCE(re.text_content, r.title || ' ' || r.content)) 
                            @@ plainto_tsquery('english', %s)
                            OR ({keyword_like_clause})
                        )
                    ORDER BY r."dateReview" DESC NULLS LAST
                    LIMIT %s;
                """
                # Execute query: params + query (for WHERE @@) + keyword_params + top_k
                all_params = list(params) + [query] + keyword_params + [top_k]
                cur.execute(query_sql, tuple(all_params))
            
            results = cur.fetchall()
            
            # Format results
            reviews = []
            for row in results:
                reviews.append({
                    'review_id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'score': float(row[3]) if row[3] else None,
                    'date_review': row[4].isoformat() if row[4] else None,
                    'route': row[5],
                    'sentiment_label': row[6],
                    'text_content': row[7],
                    'similarity': float(row[8]) if row[8] else 0.0
                })
            
            return reviews
            
        finally:
            cur.close()
            conn.close()
    
    def generate_answer(
        self,
        query: str,
        reviews: List[Dict],
        max_evidence: int = 5
    ) -> Dict:
        """
        Generate answer using DeepSeek API
        
        Args:
            query: User query
            reviews: Retrieved review list
            max_evidence: Maximum number of cited reviews
            
        Returns:
            Dictionary containing answer, evidence, and suggestions
        """
        if not DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY not set")
        
        if not reviews:
            return {
                'answer': 'No relevant reviews found for your query.',
                'pain_points': [],
                'positive_aspects': [],
                'evidence': [],
                'actions': [],
                'query_type': 'unknown'
            }
        
        # Select top max_evidence most relevant reviews as evidence
        evidence_reviews = reviews[:max_evidence]
        
        # Detect query nature (positive or negative)
        query_lower = query.lower()
        is_positive_query = any(keyword in query_lower for keyword in [
            'positive', 'good', 'strength', 'strong', 'excellent', 'great', 
            'best', 'benefit', 'advantage', 'pro', 'praise', 'compliment',
            'appreciate', 'like', 'love', 'enjoy', 'satisfied', 'happy',
            'well', 'better', 'improve', 'improved', 'enhance', 'enhanced'
        ])
        
        # Adjust structure and field names based on query nature
        if is_positive_query:
            main_section = "Positive Aspects"
            main_field = "positive_aspects"
            section_description = "List the main strengths/positive aspects mentioned in the reviews"
        else:
            main_section = "Pain Points"
            main_field = "pain_points"
            section_description = "List the main issues/problems mentioned in the reviews"
        
        # Build prompt
        evidence_text = "\n\n".join([
            f"[Review {i+1} - ID: {rev['review_id']}]\n"
            f"Title: {rev.get('title', '')}\n"
            f"Content: {rev.get('content', '')}\n"
            f"Rating: {rev.get('score', 'N/A')}/10\n"
            f"Date: {rev.get('date_review', 'N/A')}"
            for i, rev in enumerate(evidence_reviews)
        ])
        
        system_prompt = f"""You are AirSight, an AI assistant specialized in analyzing airline reviews. 
Your task is to answer questions based ONLY on the provided review evidence. 

IMPORTANT RULES:
1. Answer ONLY based on the provided reviews. Do not use external knowledge.
2. Structure your answer in three sections:
   - {main_section}: {section_description}
   - Evidence: Cite specific review excerpts (use Review ID format: [Review 1 - ID: xxx])
   - Actions: Provide 3 actionable recommendations based on the evidence

3. Be specific and cite review IDs for each claim.
4. If the evidence is insufficient, say so clearly.
5. Use clear, professional language.
6. Focus on what the user is asking for (positive aspects OR pain points)."""
        
        user_prompt = f"""Question: {query}

Evidence from reviews:
{evidence_text}

Please provide a structured answer with:
1. {main_section} (list main {"positive aspects" if is_positive_query else "issues"})
2. Evidence (cite specific reviews with IDs)
3. Actions (3 actionable recommendations)

Format your answer as JSON with the following structure:
{{
    "{main_field}": ["point 1", "point 2", ...],
    "evidence": [
        {{
            "review_id": "xxx",
            "excerpt": "relevant text from review",
            "point": "which {"positive aspect" if is_positive_query else "pain point"} this supports"
        }},
        ...
    ],
    "actions": ["action 1", "action 2", "action 3"],
    "summary": "brief summary"
}}"""
        
        # Call DeepSeek API
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            answer_text = result['choices'][0]['message']['content']
            
            # Try to parse JSON (if LLM returns JSON)
            try:
                # Extract JSON part (may be in markdown code block)
                if '```json' in answer_text:
                    json_start = answer_text.find('```json') + 7
                    json_end = answer_text.find('```', json_start)
                    answer_text = answer_text[json_start:json_end].strip()
                elif '```' in answer_text:
                    json_start = answer_text.find('```') + 3
                    json_end = answer_text.find('```', json_start)
                    answer_text = answer_text[json_start:json_end].strip()
                
                answer_data = json.loads(answer_text)
            except json.JSONDecodeError:
                # If not JSON, parse as text
                answer_data = {
                    'summary': answer_text,
                    'pain_points': [],
                    'positive_aspects': [],
                    'evidence': [],
                    'actions': []
                }
            
            # Ensure evidence contains review_id
            for ev in answer_data.get('evidence', []):
                if 'review_id' not in ev:
                    # Try to extract from text
                    for rev in evidence_reviews:
                        if rev['review_id'] in str(ev):
                            ev['review_id'] = rev['review_id']
                            break
            
            # Unify fields: return corresponding fields based on query nature
            if is_positive_query:
                return {
                    'answer': answer_data.get('summary', answer_text),
                    'positive_aspects': answer_data.get('positive_aspects', []),
                    'pain_points': [],  # Ensure frontend can check
                    'evidence': answer_data.get('evidence', []),
                    'actions': answer_data.get('actions', []),
                    'raw_response': answer_text,
                    'query_type': 'positive'
                }
            else:
                return {
                    'answer': answer_data.get('summary', answer_text),
                    'pain_points': answer_data.get('pain_points', []),
                    'positive_aspects': [],  # Ensure frontend can check
                    'evidence': answer_data.get('evidence', []),
                    'actions': answer_data.get('actions', []),
                    'raw_response': answer_text,
                    'query_type': 'negative'
                }
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"DeepSeek API error: {e}")
        except Exception as e:
            raise ValueError(f"Error processing response: {e}")
    
    def ask_question(
        self,
        query: str,
        airline_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        destination: Optional[str] = None,
        sentiment: Optional[str] = None,
        top_k: int = 10,
        max_evidence: int = 5
    ) -> Dict:
        """
        Complete RAG flow: retrieve + generate answer
        
        Returns:
            Complete result containing answer, evidence, and suggestions
        """
        # 1. Retrieve relevant reviews
        reviews = self.retrieve_reviews(
            query=query,
            airline_name=airline_name,
            start_date=start_date,
            end_date=end_date,
            destination=destination,
            sentiment=sentiment,
            top_k=top_k
        )
        
        # 2. Generate answer
        answer = self.generate_answer(query, reviews, max_evidence=max_evidence)
        
        # 3. Return complete result
        return {
            'query': query,
            'airline_name': airline_name,
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'destination': destination,
                'sentiment': sentiment
            },
            'retrieved_reviews_count': len(reviews),
            'answer': answer,
            'all_reviews': reviews[:max_evidence]  # Return first max_evidence reviews for display
        }


if __name__ == "__main__":
    # Test
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    dsn = os.getenv("POSTGRES_DSN")
    
    service = RAGService(dsn)
    
    result = service.ask_question(
        query="What are the main complaints about Delta Air Lines in the last 3 months?",
        airline_name="Delta Air Lines",
        top_k=10,
        max_evidence=5
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

