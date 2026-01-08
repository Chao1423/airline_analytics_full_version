#!/usr/bin/env python3
"""
Sentiment Analysis Pipeline
Reads review text from reviews table, generates reviews_clean and reviews_sentiment tables
Supports incremental updates, only processes new reviews
"""

import psycopg
from dotenv import load_dotenv
import os
from datetime import datetime, date
from sentModel import sentModel
import re
from typing import Dict, List, Tuple, Optional
import json

# Language detection library (using langdetect, lightweight)
try:
    from langdetect import detect, LangDetectException
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    print("⚠️  langdetect not available. Install with: pip install langdetect")

load_dotenv()
POSTGRES_DSN = os.getenv("POSTGRES_DSN")

class SentimentPipeline:
    def __init__(self, dsn: str):
        self.conn = psycopg.connect(dsn)
        self.cur = self.conn.cursor()
        self.sent_model = sentModel()
        self.stats = {
            'total_processed': 0,
            'success': 0,
            'failed': 0,
            'skipped_empty': 0,
            'skipped_non_english': 0,
            'translated': 0,
            'errors': []
        }
    
    def clean_text(self, text: str) -> str:
        """Clean text (preserve original text for sentiment analysis, only basic cleaning)"""
        if not text:
            return ""
        
        # Basic cleaning: remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        # Remove extra spaces
        text = text.strip()
        
        # Note: Do not over-clean, preserve original text features for sentiment analysis
        # sentModel has its own sentence_cleaner method
        
        return text
    
    def detect_language(self, text: str) -> Optional[str]:
        """Detect text language"""
        if not LANGDETECT_AVAILABLE:
            # Simple heuristic: if most characters are ASCII, assume English
            ascii_ratio = sum(1 for c in text if ord(c) < 128) / len(text) if text else 0
            return 'en' if ascii_ratio > 0.9 else None
        
        try:
            lang = detect(text)
            return lang
        except LangDetectException:
            return None
    
    def translate_text(self, text: str, target_lang: str = 'en') -> Optional[str]:
        """
        Translate text to target language
        Note: This is a placeholder, can use googletrans or other translation APIs
        For production, recommend using paid translation API (e.g., Google Cloud Translation)
        """
        # Placeholder implementation: return None to indicate translation not supported
        # Actual implementation can use:
        # from googletrans import Translator
        # translator = Translator()
        # result = translator.translate(text, dest=target_lang)
        # return result.text
        
        # Current strategy: filter non-English reviews (see process_reviews method)
        return None
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count (simple implementation: split by spaces)"""
        if not text:
            return 0
        return len(text.split())
    
    def process_review(self, review_id: str, airline_name: str, content: str, review_date: Optional[date]) -> Tuple[bool, Optional[str]]:
        """
        Process a single review
        Returns: (success, error_message)
        """
        try:
            # 1. Clean text
            cleaned_text = self.clean_text(content)
            
            if not cleaned_text or len(cleaned_text.strip()) < 10:
                return False, "Empty or too short text after cleaning"
            
            # 2. Detect language
            lang = self.detect_language(cleaned_text)
            
            # 3. Handle non-English reviews
            # Strategy: Filter non-English reviews (because sentiment analysis model is English)
            # Reasons:
            # - Translation quality may affect sentiment analysis accuracy
            # - Translation API has cost and rate limits
            # - English reviews usually make up the majority
            # If multi-language support is needed, can:
            # 1. Use multi-language sentiment analysis model
            # 2. Integrate translation API (e.g., Google Cloud Translation)
            if lang and lang != 'en':
                return False, f"Non-English language detected: {lang}"
            
            # 4. Calculate token count
            tokens_count = self.count_tokens(cleaned_text)
            
            # 5. Extract month
            review_month = review_date.replace(day=1) if review_date else None
            
            # 6. Insert or update reviews_clean
            self.cur.execute(
                """
                INSERT INTO reviews_clean (
                    review_id, "airlineName", cleaned_text, lang, review_month, tokens_count
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (review_id, "airlineName") 
                DO UPDATE SET
                    cleaned_text = EXCLUDED.cleaned_text,
                    lang = EXCLUDED.lang,
                    review_month = EXCLUDED.review_month,
                    tokens_count = EXCLUDED.tokens_count,
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (review_id, airline_name, cleaned_text, lang, review_month, tokens_count)
            )
            
            # 7. Sentiment analysis
            try:
                score, sent_lab, pos_dict, neg_dict = self.sent_model.run_score(cleaned_text, num_features=10)
                
                # Normalize sentiment_score to -1.0 to 1.0
                sentiment_score = float(score)
                
                # 8. Insert or update reviews_sentiment
                self.cur.execute(
                    """
                    INSERT INTO reviews_sentiment (
                        review_id, "airlineName", sentiment_label, sentiment_score, model_name
                    ) VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (review_id, "airlineName")
                    DO UPDATE SET
                        sentiment_label = EXCLUDED.sentiment_label,
                        sentiment_score = EXCLUDED.sentiment_score,
                        model_name = EXCLUDED.model_name,
                        updated_at = CURRENT_TIMESTAMP;
                    """,
                    (review_id, airline_name, sent_lab, sentiment_score, 'cardiffnlp/twitter-roberta-base-sentiment-latest')
                )
                
                self.conn.commit()
                return True, None
                
            except Exception as e:
                self.conn.rollback()
                return False, f"Sentiment analysis failed: {str(e)}"
                
        except Exception as e:
            self.conn.rollback()
            return False, str(e)
    
    def get_new_reviews(self, batch_size: int = 100) -> List[Tuple]:
        """
        Get new reviews that need processing (incremental update)
        Only returns reviews that are not yet in reviews_clean table
        """
        self.cur.execute(
            """
            SELECT 
                r."reviewId",
                r."airlineName",
                r.content,
                r."dateReview"
            FROM reviews r
            LEFT JOIN reviews_clean rc 
                ON r."reviewId" = rc.review_id 
                AND r."airlineName" = rc."airlineName"
            WHERE r.content IS NOT NULL
                AND r.content != ''
                AND rc.review_id IS NULL
            ORDER BY r."dateReview" DESC NULLS LAST
            LIMIT %s;
            """,
            (batch_size,)
        )
        return self.cur.fetchall()
    
    def process_batch(self, batch_size: int = 100, max_reviews: Optional[int] = None):
        """
        Process a batch of reviews
        """
        processed_count = 0
        
        while True:
            reviews = self.get_new_reviews(batch_size)
            
            if not reviews:
                break
            
            for review_id, airline_name, content, review_date in reviews:
                if max_reviews and processed_count >= max_reviews:
                    break
                
                self.stats['total_processed'] += 1
                
                if not content or len(content.strip()) < 10:
                    self.stats['skipped_empty'] += 1
                    continue
                
                success, error = self.process_review(review_id, airline_name, content, review_date)
                
                if success:
                    self.stats['success'] += 1
                else:
                    self.stats['failed'] += 1
                    if error:
                        if 'Non-English' in error:
                            self.stats['skipped_non_english'] += 1
                        elif 'Empty' in error:
                            self.stats['skipped_empty'] += 1
                        else:
                            self.stats['errors'].append({
                                'review_id': review_id,
                                'error': error
                            })
                
                processed_count += 1
            
            if max_reviews and processed_count >= max_reviews:
                break
    
    def generate_report(self) -> Dict:
        """Generate data quality report"""
        # Get statistics
        self.cur.execute("SELECT COUNT(*) FROM reviews_clean;")
        total_clean = self.cur.fetchone()[0]
        
        self.cur.execute("SELECT COUNT(*) FROM reviews_sentiment;")
        total_sentiment = self.cur.fetchone()[0]
        
        self.cur.execute("""
            SELECT COUNT(*) 
            FROM reviews 
            WHERE content IS NOT NULL AND content != '';
        """)
        total_reviews = self.cur.fetchone()[0]
        
        self.cur.execute("""
            SELECT COUNT(*) 
            FROM reviews_clean 
            WHERE cleaned_text IS NULL OR cleaned_text = '';
        """)
        empty_clean = self.cur.fetchone()[0]
        
        empty_ratio = (empty_clean / total_clean * 100) if total_clean > 0 else 0
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'processing_stats': {
                'total_processed': self.stats['total_processed'],
                'success': self.stats['success'],
                'failed': self.stats['failed'],
                'skipped_empty': self.stats['skipped_empty'],
                'skipped_non_english': self.stats['skipped_non_english'],
                'translated': self.stats['translated']
            },
            'database_stats': {
                'total_reviews': total_reviews,
                'total_clean': total_clean,
                'total_sentiment': total_sentiment,
                'empty_text_ratio': round(empty_ratio, 2)
            },
            'errors': self.stats['errors'][:10]  # Show only first 10 errors
        }
        
        return report
    
    def close(self):
        if self.conn:
            self.cur.close()
            self.conn.close()


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process reviews for sentiment analysis')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for processing')
    parser.add_argument('--max-reviews', type=int, default=None, help='Maximum number of reviews to process')
    parser.add_argument('--report-only', action='store_true', help='Only generate report, do not process')
    
    args = parser.parse_args()
    
    if not POSTGRES_DSN:
        print("❌ POSTGRES_DSN not found in environment variables")
        return
    
    pipeline = SentimentPipeline(POSTGRES_DSN)
    
    try:
        if not args.report_only:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔄 Starting sentiment pipeline...")
            print(f"Batch size: {args.batch_size}")
            if args.max_reviews:
                print(f"Max reviews: {args.max_reviews}")
            print()
            
            pipeline.process_batch(batch_size=args.batch_size, max_reviews=args.max_reviews)
        
        # Generate report
        report = pipeline.generate_report()
        
        print("\n" + "="*60)
        print("📊 Data Quality Report")
        print("="*60)
        print(f"\nProcessing Stats:")
        print(f"  Total Processed: {report['processing_stats']['total_processed']}")
        print(f"  Success: {report['processing_stats']['success']}")
        print(f"  Failed: {report['processing_stats']['failed']}")
        print(f"  Skipped (Empty): {report['processing_stats']['skipped_empty']}")
        print(f"  Skipped (Non-English): {report['processing_stats']['skipped_non_english']}")
        print(f"  Translated: {report['processing_stats']['translated']}")
        
        print(f"\nDatabase Stats:")
        print(f"  Total Reviews: {report['database_stats']['total_reviews']}")
        print(f"  Total Clean: {report['database_stats']['total_clean']}")
        print(f"  Total Sentiment: {report['database_stats']['total_sentiment']}")
        print(f"  Empty Text Ratio: {report['database_stats']['empty_text_ratio']}%")
        
        if report['errors']:
            print(f"\nErrors (showing first 10):")
            for error in report['errors']:
                print(f"  Review {error['review_id']}: {error['error']}")
        
        print("\n" + "="*60)
        
        # Save report to file
        report_file = f"sentiment_pipeline_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"✅ Report saved to: {report_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pipeline.close()


if __name__ == "__main__":
    main()

