from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from postgres_db import PostgresClient
from dotenv import load_dotenv
import os
from datetime import datetime
from sentModel import sentModel
import numpy as np
from sklearn.linear_model import LinearRegression
from typing import Optional, List, Dict

load_dotenv()
POSTGRES_DSN = os.getenv("POSTGRES_DSN")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def welcome():
    return {"message": "Welcome to the Airline Review API 👋"}

@app.get("/airlines/top-rated")
async def get_top_rated_airlines(
    min_reviews: int = Query(50, ge=1, description="Minimum number of reviews required (default: 50)"),
    use_weighted: bool = Query(True, description="Use weighted ranking (Bayesian average) (default: True)")
):
    """
    Get top rated airlines with weighted ranking
    
    Uses Bayesian average to balance rating and review count:
    - Airlines with few reviews are pulled toward the global average
    - Airlines with many reviews maintain their rating
    - min_reviews: Minimum review count threshold
    - use_weighted: Enable weighted ranking (recommended)
    """
    db = PostgresClient(POSTGRES_DSN)
    try:
        airlines = db.get_top_rated_airlines(min_reviews=min_reviews, use_weighted_ranking=use_weighted)
        return {"status": "success", "data": airlines}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/airlines/{airline_name}/key-data")
async def get_airline_key_data(airline_name: str):
    """Get key data for a specific airline"""
    db = PostgresClient(POSTGRES_DSN)
    try:
        data = db.get_airline_key_data(airline_name)
        
        if not data:
            raise HTTPException(status_code=404, detail="Airline not found")
        
        return {"status": "success", "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/airlines/{airline_name}/rating-distribution")
async def get_rating_distribution(
    airline_name: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    destination: Optional[str] = Query(None, description="Destination city name")
):
    """Get rating distribution (1-5) for a specific airline with optional filters"""
    db = PostgresClient(POSTGRES_DSN)
    try:
        # Always use filtered version for rating distribution (1-5)
        data = db.get_rating_distribution_filtered(airline_name, start_date, end_date, destination)
        
        if not data:
            return {"status": "success", "data": []}
        
        return {"status": "success", "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/airlines/{airline_name}/kpis")
async def get_airline_kpis(
    airline_name: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    destination: Optional[str] = Query(None, description="Destination city name")
):
    """Get KPI metrics for a specific airline with optional filters"""
    db = PostgresClient(POSTGRES_DSN)
    try:
        data = db.get_airline_kpis(airline_name, start_date, end_date, destination)
        
        if not data:
            raise HTTPException(status_code=404, detail="No data found for this airline")
        
        return {"status": "success", "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/airlines/{airline_name}/sub-item-scoring")
async def get_sub_item_scoring(
    airline_name: str,
    use_sentiment: bool = Query(False, description="Use aspect-based sentiment analysis (default: False, uses rating data)")
):
    """
    Get sub-item scoring comparison for a specific airline
    
    - use_sentiment=False: Uses rating data from reviews table (faster, more reliable)
    - use_sentiment=True: Uses aspect-based sentiment analysis from sentiment pipeline (requires processed reviews)
    """
    db = PostgresClient(POSTGRES_DSN)
    try:
        if use_sentiment:
            # Use aspect-based sentiment analysis
            data = db.get_aspect_sentiment_scoring(airline_name)
        else:
            # Use rating data (default)
            data = db.get_sub_item_scoring(airline_name)
        
        if not data:
            raise HTTPException(status_code=404, detail="Airline not found or insufficient data")
        
        return {"status": "success", "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/airlines/{airline_name}/city-distribution")
async def get_airline_city_distribution(airline_name: str, cities_csv: str = "worldcities.csv"):
    """Get city distribution for airline routes"""
    db = PostgresClient(POSTGRES_DSN)
    try:
        data = db.get_airline_city_distribution(airline_name, cities_csv)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/airlines/{airline_name}/info")
async def get_airline_info(airline_name: str):
    """Get airline name and image"""
    db = PostgresClient(POSTGRES_DSN)
    try:
        data = db.get_airline_info(airline_name)
        
        if not data:
            raise HTTPException(status_code=404, detail="Airline not found")
        
        return {"status": "success", "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/airlines/{airline_name}/reviews")
async def get_airline_reviews(airline_name: str):
    """Get airline reviews with optional keyword filtering in content"""
    db = PostgresClient(POSTGRES_DSN)
    try:
        data = db.get_reviews_by_airline(airline_name)
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/sentiment-tool/submit")
async def submit_sentiment_text(text: str = Body(...)):
    """Submit text for sentiment analysis"""
    db = PostgresClient(POSTGRES_DSN)
    try:
        if not text:
            raise HTTPException(status_code=404, detail="Text field is required")
        
        sm = sentModel()
        score, sent_lab, pos_dict, neg_dict = sm.run_score(text, num_features=50)
        submit_time = datetime.utcnow()
        
        db.insert_sentiment(text, submit_time, sent_lab, pos_dict, neg_dict)
        
        return {
            "status": "success",
            "data": {
                "text": text,
                "score": float(score),
                "sent_lab": sent_lab,
                "pos_dict": pos_dict,
                "neg_dict": neg_dict
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/airlines/{airline_name}/wordcloud-data")
async def get_airline_wordcloud_data(airline_name: str):
    """Get wordcloud data from random airline reviews"""
    db = PostgresClient(POSTGRES_DSN)
    try:
        reviews = db.get_random_reviews(airline_name, limit=10)
        
        if not reviews:
            raise HTTPException(status_code=404, detail="No reviews found for this airline")
        
        sm = sentModel()
        combined_pos_dict = {}
        combined_neg_dict = {}
        
        for review in reviews:
            content = review.get('content', '')
                
            _, _, pos_dict, neg_dict = sm.run_score(content)
            
            for word, metrics in pos_dict.items():
                if word in combined_pos_dict:
                    combined_pos_dict[word]['score'] += metrics['score']
                else:
                    combined_pos_dict[word] = {'score': metrics['score']}
            
            for word, metrics in neg_dict.items():
                if word in combined_neg_dict:
                    combined_neg_dict[word]['score'] += metrics['score']
                else:
                    combined_neg_dict[word] = {'score': metrics['score']}
        
        pos_score = sum(abs(m['score']) for m in combined_pos_dict.values())
        neg_score = sum(abs(m['score']) for m in combined_neg_dict.values())
        pos_count = len(combined_pos_dict)
        neg_count = len(combined_neg_dict)
        overall_score = pos_score - neg_score
        overall_count = pos_count + neg_count
        
        return {
            "status": "success",
            "data": {
                "pos_dict": combined_pos_dict,
                "neg_dict": combined_neg_dict,
                "pos_score": float(pos_score),
                "neg_score": float(-neg_score),
                "overall_score": float(overall_score),
                "pos_count": pos_count,
                "neg_count": neg_count,
                "overall_count": overall_count,
                "review_count": len(reviews)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/airlines/{airline_name}/monthly-trends")
async def get_monthly_trends(
    airline_name: str,
    start_date: Optional[str] = Query('2020-01-01', description="Start date (YYYY-MM-DD), default: 2020-01-01"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD), default: today"),
    top_n_destinations: int = Query(5, description="Number of top destinations per month, default: 5")
):
    """Get monthly trends for an airline"""
    db = PostgresClient(POSTGRES_DSN)
    try:
        data = db.get_monthly_trends(airline_name, start_date, end_date, top_n_destinations)
        
        if not data:
            return {"status": "success", "data": []}
        
        return {"status": "success", "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/airlines/{airline_name}/rating-distribution-by-segment")
async def get_rating_distribution_by_segment(
    airline_name: str,
    segment: str = Query('seatType', description="Segment field: seatType, typeOfTraveller, country, aircraft"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    destination: Optional[str] = Query(None, description="Destination city name"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of segments to return (1-50, top N by review count)")
):
    """Get rating distribution (1-5) grouped by segment
    
    For segments with many values (like country or aircraft), this endpoint:
    - Returns only top N segments by total review count (limit)
    - Helps prevent chart overcrowding and improves readability
    - No minimum review count requirement - shows all segments up to the limit
    """
    db = PostgresClient(POSTGRES_DSN)
    try:
        data = db.get_rating_distribution_by_segment(airline_name, segment, start_date, end_date, destination, limit)
        
        if not data:
            return {"status": "success", "data": []}
        
        return {"status": "success", "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/airlines/{airline_name}/monthly-trends")
async def get_monthly_trends(
    airline_name: str,
    start_date: Optional[str] = Query('2020-01-01', description="Start date (YYYY-MM-DD), default: 2020-01-01"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD), default: today"),
    destination_top_n: int = Query(5, ge=1, le=10, description="Number of top destinations to include (1-10)"),
    use_materialized_view: bool = Query(False, description="Use materialized view for faster query (may be stale)")
):
    """Get monthly trends for an airline
    
    Returns monthly aggregated data:
    - review_count: Number of reviews per month
    - avg_rating: Average rating per month
    - sentiment_mean: Average sentiment score (placeholder, currently null)
    - destination_topN: Top N destinations per month
    
    Performance: Set use_materialized_view=True for faster queries on large datasets.
    The materialized view should be refreshed regularly via cron job.
    """
    db = PostgresClient(POSTGRES_DSN)
    try:
        data = db.get_monthly_trends(airline_name, start_date, end_date, destination_top_n, use_materialized_view)
        
        if not data:
            return {"status": "success", "data": []}
        
        return {"status": "success", "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/airlines/{airline_name}/feature-importance")
async def get_airline_feature_importance_old(airline_name: str):
    """Legacy endpoint - Get feature importance from linear regression on airline reviews (using rating fields)"""
    db = PostgresClient(POSTGRES_DSN)
    try:
        reviews = db.get_reviews_for_regression(airline_name)
        
        if not reviews or len(reviews) < 10:
            raise HTTPException(status_code=404, detail="Not enough reviews for regression analysis")
        
        X = []
        y = []
        feature_names = [
            'seatComfort', 'cabinStaffService', 'foodBeverages',
            'inflightEntertainment', 'groundService', 'wifiConnectivity', 'valueForMoney'
        ]
        
        for review in reviews:
            features = [
                review.get('seatComfort', 0) or 0,
                review.get('cabinStaffService', 0) or 0,
                review.get('foodBeverages', 0) or 0,
                review.get('inflightEntertainment', 0) or 0,
                review.get('groundService', 0) or 0,
                review.get('wifiConnectivity', 0) or 0,
                review.get('valueForMoney', 0) or 0
            ]
            X.append(features)
            y.append(review.get('score', 0) or 0)
        
        X = np.array(X)
        y = np.array(y)
        
        model = LinearRegression()
        model.fit(X, y)
        
        coefficients = {
            feature_names[i]: float(model.coef_[i])
            for i in range(len(feature_names))
        }
        
        return {
            "status": "success",
            "data": coefficients
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/airlines/{airline_name}/feature-importance")
async def get_airline_feature_importance_api(
    airline_name: str,
    compute: bool = Query(False, description="Force recompute topic importance (default: False, uses cached)")
):
    """
    Get feature importance from OLS regression on topic shares
    
    Uses topic-based analysis:
    - Input: reviews table with ratings, reviews_topics table with topic shares
    - Method: OLS regression (rating ~ topic_1 + topic_2 + ... + topic_k)
    - Output: coefficients, confidence intervals, p-values
    
    Returns:
    - topic_label: Topic identifier/label
    - coef: Regression coefficient
    - ci_low: 95% confidence interval lower bound
    - ci_high: 95% confidence interval upper bound
    - p_value: Statistical significance
    - model_r_squared: Model fit (R²)
    - sample_size: Number of reviews used
    """
    db = PostgresClient(POSTGRES_DSN)
    try:
        # Try to get cached results
        if not compute:
            data = db.get_topic_importance(airline_name, use_cached=True)
            if data:
                return {"status": "success", "data": data}
        
        # If no cache or force compute, run analysis
        data = db.compute_topic_importance(airline_name, min_samples=30)
        
        if not data:
            raise HTTPException(
                status_code=404, 
                detail="No topic importance data available. Ensure reviews_topics table has data and sufficient samples (30+ reviews)."
            )
        
        return {"status": "success", "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
@app.get("/api/airlines/{airline_name}/top-topics")
async def get_top_topics(
    airline_name: str,
    sentiment: str = Query('pos', description="Sentiment bucket: 'pos' or 'neg' (default: 'pos')"),
    n: int = Query(10, ge=1, le=50, description="Number of topics to return (1-50, default: 10)")
):
    """
    Get top topics for an airline by sentiment
    
    Returns top N topics (by review count) for positive or negative reviews:
    - topic_id: Topic identifier
    - top_words: List of top keywords for the topic
    - human_label: Human-readable topic label
    - review_count: Number of reviews associated with this topic
    - avg_score: Average topic score/probability
    """
    if sentiment not in ['pos', 'neg']:
        raise HTTPException(status_code=400, detail="sentiment must be 'pos' or 'neg'")
    
    db = PostgresClient(POSTGRES_DSN)
    try:
        topics = db.get_top_topics(airline_name, sentiment, n)
        
        if not topics:
            return {"status": "success", "data": []}
        
        return {"status": "success", "data": topics}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/reviews/search")
async def search_reviews(
    airline_name: str = Query(..., description="Airline name"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    min_rating: Optional[int] = Query(None, ge=0, le=10, description="Minimum rating (0-10)"),
    max_rating: Optional[int] = Query(None, ge=0, le=10, description="Maximum rating (0-10)"),
    sentiment: Optional[str] = Query(None, description="Sentiment: 'pos', 'neg', or 'neutral'"),
    topic_id: Optional[int] = Query(None, description="Topic ID"),
    aspect: Optional[str] = Query(None, description="Aspect name (e.g., 'Seat Comfort', 'Cabin Staff & Service')"),
    destination: Optional[str] = Query(None, description="Destination keyword"),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(20, ge=1, le=100, description="Page size (1-100)")
):
    """
    Search reviews with advanced filtering and pagination
    
    Returns:
    - reviews: List of review objects with topic/aspect information
    - pagination: Page info (page, page_size, total_count, total_pages)
    - summary: Aggregated statistics (count, avg_rating, top_topics, top_aspects)
    """
    db = PostgresClient(POSTGRES_DSN)
    try:
        result = db.search_reviews(
            airline_name=airline_name,
            start_date=start_date,
            end_date=end_date,
            min_rating=min_rating,
            max_rating=max_rating,
            sentiment=sentiment,
            topic_id=topic_id,
            aspect=aspect,
            destination=destination,
            page=page,
            page_size=page_size
        )
        
        if not result:
            return {
                "status": "success",
                "data": {
                    "reviews": [],
                    "pagination": {"page": page, "page_size": page_size, "total_count": 0, "total_pages": 0},
                    "summary": {"count": 0, "avg_rating": None, "top_topics": [], "top_aspects": []}
                }
            }
        
        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/airlines/{airline_name}/drivers")
async def get_topic_drivers(
    airline_name: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    compute: bool = Query(False, description="Force recompute (default: False, uses cached)"),
    min_samples: int = Query(30, ge=10, le=1000, description="Minimum number of reviews required (default: 30)"),
    auto_mine: bool = Query(True, description="Automatically run topic mining if data is missing")
):
    """
    Get topic drivers (OLS regression results showing which topics drive ratings)
    
    Returns topics sorted by coefficient:
    - Positive coefficients: topics that increase ratings
    - Negative coefficients: topics that decrease ratings
    
    Each topic includes:
    - topic_id, topic_label, top_words
    - coef: Regression coefficient
    - se: Standard error
    - p_value: Statistical significance
    - ci_low, ci_high: 95% confidence interval
    """
    db = PostgresClient(POSTGRES_DSN)
    try:
        model_spec = 'default'
        if start_date or end_date:
            model_spec = f"range_{start_date or 'all'}_{end_date or 'all'}"
        
        # Try to get cached results
        if not compute:
            data = db.get_topic_drivers(airline_name, model_spec, use_cached=True)
            if data:
                return {"status": "success", "data": data}
        
        # Check if topic data exists
        topic_check_conditions = ['LOWER(rt."airlineName") = LOWER(%s)']
        topic_check_params = [airline_name]
        
        if start_date:
            topic_check_conditions.append('r."dateReview" >= %s')
            topic_check_params.append(start_date)
        if end_date:
            topic_check_conditions.append('r."dateReview" <= %s')
            topic_check_params.append(end_date)
        
        topic_check_clause = ' AND '.join(topic_check_conditions)
        
        db.cur.execute(
            f"""
            SELECT COUNT(DISTINCT rt.review_id)
            FROM reviews_topics rt
            JOIN reviews r ON rt.review_id = r."reviewId"
            WHERE {topic_check_clause}
            """,
            tuple(topic_check_params)
        )
        topic_count = db.cur.fetchone()[0]
        
        # If no topic data and auto_mine is True, return needs_mining status
        if topic_count == 0 and auto_mine:
            return {
                "status": "needs_mining",
                "message": "No topic data available. Topic mining is required.",
                "airline_name": airline_name,
                "start_date": start_date,
                "end_date": end_date
            }
        
        # If no cache or force compute, run analysis
        data = db.compute_topic_drivers(airline_name, start_date, end_date, min_samples=min_samples, model_spec=model_spec)
        
        if not data:
            raise HTTPException(
                status_code=404, 
                detail=f"No topic driver data available for {airline_name}. Need at least {min_samples} reviews with BOTH rating and topic data. "
                       f"Note: This requires REVIEWS (not topics) - each review must have topic assignments from topic mining pipeline. "
                       f"Try running topic mining pipeline, use a different airline/time range, or lower min_samples parameter."
            )
        
        return {"status": "success", "data": data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/api/topic-mining/run")
async def run_topic_mining(
    airline_name: str = Body(..., description="Airline name"),
    start_date: Optional[str] = Body(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Body(None, description="End date (YYYY-MM-DD)"),
    sentiment: str = Body("both", description="Sentiment bucket: 'pos', 'neg', or 'both'"),
    min_topic_size: int = Body(10, description="Minimum topic size")
):
    """
    Run topic mining for a specific airline and date range
    
    This endpoint will:
    1. Check if sentiment data exists for the airline/date range
    2. Run topic mining if data is available
    3. Return the status and results
    """
    from topic_mining import TopicMiner
    import psycopg
    
    db = PostgresClient(POSTGRES_DSN)
    try:
        # Check if sentiment data exists
        where_conditions = ['LOWER(rs."airlineName") = LOWER(%s)']
        params = [airline_name]
        
        if start_date:
            where_conditions.append('r."dateReview" >= %s')
            params.append(start_date)
        if end_date:
            where_conditions.append('r."dateReview" <= %s')
            params.append(end_date)
        
        where_clause = ' AND '.join(where_conditions)
        
        db.cur.execute(
            f"""
            SELECT COUNT(DISTINCT rs.review_id)
            FROM reviews_sentiment rs
            JOIN reviews r ON rs.review_id = r."reviewId"
            WHERE {where_clause}
            """,
            tuple(params)
        )
        sentiment_count = db.cur.fetchone()[0]
        
        if sentiment_count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No sentiment data available for {airline_name} in the specified date range. Please run sentiment pipeline first."
            )
        
        # Run topic mining
        conn = psycopg.connect(POSTGRES_DSN)
        try:
            miner = TopicMiner(
                airline_name=airline_name,
                min_topic_size=min_topic_size,
                n_topics=None,
                start_date=start_date,
                end_date=end_date
            )
            
            results = {
                "pos": {"topics_created": 0, "reviews_processed": 0},
                "neg": {"topics_created": 0, "reviews_processed": 0}
            }
            
            if sentiment in ['pos', 'both']:
                miner.mine_topics(conn, 'pos')
                # Get processing results
                db.cur.execute(
                    """
                    SELECT COUNT(DISTINCT topic_id), COUNT(DISTINCT review_id)
                    FROM reviews_topics
                    WHERE LOWER("airlineName") = LOWER(%s) AND sentiment_bucket = 'pos'
                    """,
                    (airline_name,)
                )
                pos_result = db.cur.fetchone()
                results["pos"] = {"topics_created": pos_result[0] or 0, "reviews_processed": pos_result[1] or 0}
            
            if sentiment in ['neg', 'both']:
                miner.mine_topics(conn, 'neg')
                # Get processing results
                db.cur.execute(
                    """
                    SELECT COUNT(DISTINCT topic_id), COUNT(DISTINCT review_id)
                    FROM reviews_topics
                    WHERE LOWER("airlineName") = LOWER(%s) AND sentiment_bucket = 'neg'
                    """,
                    (airline_name,)
                )
                neg_result = db.cur.fetchone()
                results["neg"] = {"topics_created": neg_result[0] or 0, "reviews_processed": neg_result[1] or 0}
            
            return {
                "status": "success",
                "message": "Topic mining completed successfully",
                "results": results
            }
        finally:
            conn.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running topic mining: {str(e)}")
    finally:
        db.close()

@app.post("/api/simulate")
async def simulate_rating_change(
    request_data: dict = Body(...)
):
    """
    Simulate rating change based on topic share changes
    
    Input:
    - airline_name: Airline to analyze
    - start_date, end_date: Optional time range
    - topic_changes: List of dicts with topic_id and share_change_pct (-50 to +50)
                     - Negative values: reduce share (for negative topics)
                     - Positive values: increase share (for positive topics)
    
    Output:
    - current_avg_rating: Current average rating
    - predicted_avg_rating: Predicted average rating after changes
    - delta_rating: Change in rating
    - delta_rating_low, delta_rating_high: Uncertainty interval
    - topic_impacts: Impact of each topic change
    - priority_rankings: Topics ranked by ROI (which topic improvement has highest ROI)
    """
    db = PostgresClient(POSTGRES_DSN)
    try:
        airline_name = request_data.get('airline_name')
        start_date = request_data.get('start_date')
        end_date = request_data.get('end_date')
        topic_changes = request_data.get('topic_changes', [])
        
        if not airline_name:
            raise HTTPException(status_code=400, detail="airline_name is required")
        if not topic_changes:
            raise HTTPException(status_code=400, detail="topic_changes is required")
        
        try:
            result = db.simulate_rating_change(airline_name, topic_changes, start_date, end_date)
        except ValueError as e:
            # Capture more detailed error information
            raise HTTPException(
                status_code=404,
                detail=str(e)
            )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Simulation failed. Ensure topic drivers are computed for this airline."
            )
        
        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/api/rag/ask")
async def ask_airsight(
    query: str = Body(..., description="User question"),
    airline_name: str = Body(..., description="Airline name"),
    start_date: Optional[str] = Body(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Body(None, description="End date (YYYY-MM-DD)"),
    destination: Optional[str] = Body(None, description="Destination keyword"),
    sentiment: Optional[str] = Body(None, description="Sentiment: 'pos', 'neg', or 'neutral'"),
    top_k: int = Body(10, ge=1, le=50, description="Number of reviews to retrieve"),
    max_evidence: int = Body(5, ge=1, le=10, description="Maximum number of evidence reviews")
):
    """
    Ask AirSight (RAG) - Answer questions based on airline reviews
    
    Returns structured answer with:
    - Pain Points: Main issues from reviews
    - Evidence: Cited review excerpts with review IDs
    - Actions: Actionable recommendations
    """
    from rag_service import RAGService
    
    try:
        service = RAGService(POSTGRES_DSN)
        result = service.ask_question(
            query=query,
            airline_name=airline_name,
            start_date=start_date,
            end_date=end_date,
            destination=destination,
            sentiment=sentiment,
            top_k=top_k,
            max_evidence=max_evidence
        )
        
        return {"status": "success", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG error: {str(e)}")
