from dotenv import load_dotenv, find_dotenv
import os
import psycopg
import json
from typing import List, Dict, Optional

load_dotenv(find_dotenv())
POSTGRES_DSN = os.getenv("POSTGRES_DSN")

class PostgresClient:
    def __init__(self, dsn):
        self.conn = psycopg.connect(dsn)
        self.cur = self.conn.cursor()

    def insert_airline(self, item):
        name = item.get("name")
        image = item.get("image")
        review_count = item.get("reviewCount")

        try:
            self.cur.execute(
                """
                INSERT INTO airlines (name, image, "reviewCount")
                VALUES (%s, %s, %s)
                ON CONFLICT (name) DO UPDATE
                SET image = EXCLUDED.image,
                    "reviewCount" = EXCLUDED."reviewCount";
                """, (name, image, review_count),
            )
        except Exception as e:
            print(f"Error inserting into airlines: {e}")
            self.conn.rollback()
        else:
            self.conn.commit()

    def insert_review(self, item):
        data = dict(item)
        required_keys = [
            "reviewId", "title", "score", "content", "verifiedType",
            "airlineName", "userName", "country", "dateReview",
            "aircraft", "typeOfTraveller", "seatType", "route", "dateFlown",
            "seatComfort", "cabinStaffService", "foodBeverages",
            "inflightEntertainment", "groundService", "wifiConnectivity",
            "valueForMoney", "recommended",
        ]

        for key in required_keys:
            if key not in data:
                if key in (
                    "score", "seatComfort", "cabinStaffService", "foodBeverages",
                    "inflightEntertainment", "groundService", "wifiConnectivity",
                    "valueForMoney", "dateReview",
                ):
                    data[key] = None
                else:
                    data[key] = ""

        try:
            self.cur.execute(
                """
                INSERT INTO reviews (
                    reviewId, userName, airlineName,
                    title, score, content, verifiedType, 
                    country, dateReview,
                    aircraft, typeOfTraveller, seatType, route, dateFlown,
                    seatComfort, cabinStaffService, foodBeverages,
                    inflightEntertainment, groundService, wifiConnectivity,
                    valueForMoney, recommended
                ) VALUES (
                    %(reviewId)s, %(userName)s, %(airlineName)s, 
                    %(title)s, %(score)s, %(content)s, %(verifiedType)s,
                    %(country)s, %(dateReview)s,
                    %(aircraft)s, %(typeOfTraveller)s, %(seatType)s, %(route)s, %(dateFlown)s,
                    %(seatComfort)s, %(cabinStaffService)s, %(foodBeverages)s,
                    %(inflightEntertainment)s, %(groundService)s, %(wifiConnectivity)s,
                    %(valueForMoney)s, %(recommended)s
                );
                """, data,
            )
        except Exception as e:
            print(f"Error inserting into reviews: {e}")
            self.conn.rollback()
        else:
            self.conn.commit()

    def get_airline_key_data(self, airline_name):
        try:
            self.cur.execute(
                """
                SELECT 
                    seatComfort,
                    cabinStaffService,
                    foodBeverages,
                    inflightEntertainment,
                    groundService,
                    wifiConnectivity,
                    valueForMoney,
                    score,
                    "calculatedReviewCount"
                FROM airlines
                WHERE LOWER(name) = LOWER(%s);
                """,
                (airline_name,)
            )
            
            airline_row = self.cur.fetchone()
            
            if not airline_row:
                return None
            
            categories = {
                'Seat Comfort': airline_row[0],
                'Cabin Staff Service': airline_row[1],
                'Food & Beverages': airline_row[2],
                'Inflight Entertainment': airline_row[3],
                'Ground Service': airline_row[4],
                'Wifi Connectivity': airline_row[5],
                'Value For Money': airline_row[6]
            }
            
            valid_categories = {k: v for k, v in categories.items() if v is not None}
            
            if valid_categories:
                top_category = max(valid_categories, key=valid_categories.get)
                top_score = valid_categories[top_category]
                lowest_category = min(valid_categories, key=valid_categories.get)
                lowest_score = valid_categories[lowest_category]
                
                top_rated_item = {
                    "score": f"{round(top_score, 1)} / 5",
                    "category": top_category
                }
                lowest_rated_item = {
                    "score": f"{round(lowest_score, 1)} / 5",
                    "category": lowest_category
                }
            else:
                top_rated_item = {
                    "score": "N/A",
                    "category": "N/A"
                }
                lowest_rated_item = {
                    "score": "N/A",
                    "category": "N/A"
                }
            
            self.cur.execute(
                """
                SELECT 
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY score) as median_score
                FROM reviews
                WHERE LOWER("airlineName") = LOWER(%s) AND score IS NOT NULL;
                """,
                (airline_name,)
            )
            median_row = self.cur.fetchone()
            median_score = int(median_row[0]) if median_row and median_row[0] else 0
            
            self.cur.execute(
                """
                SELECT 
                    COUNT(*) + 1 as rank,
                    (SELECT COUNT(*) FROM airlines) as total_airlines
                FROM airlines
                WHERE "calculatedReviewCount" > (
                    SELECT "calculatedReviewCount" 
                    FROM airlines 
                    WHERE LOWER(name) = LOWER(%s)
                );
                """,
                (airline_name,)
            )
            rank_row = self.cur.fetchone()
            rank = rank_row[0] if rank_row else 0
            total_airlines = rank_row[1] if rank_row else 0
            
            self.cur.execute(
                """
                SELECT 
                    MODE() WITHIN GROUP (ORDER BY seatType) as preferred_seat,
                    MODE() WITHIN GROUP (ORDER BY route) as preferred_route,
                    MIN(dateReview) as earliest_review,
                    MAX(dateReview) as latest_review,
                    TO_CHAR(MIN(
                        CASE 
                            WHEN dateFlown ~ '^[A-Za-z]+\s+\d{4}$'
                            THEN TO_DATE(dateFlown, 'FMMonth YYYY')
                            ELSE NULL
                        END
                    ), 'YYYY-MM') as earliest_flight,
                    TO_CHAR(MAX(
                        CASE 
                            WHEN dateFlown ~ '^[A-Za-z]+\s+\d{4}$'
                            THEN TO_DATE(dateFlown, 'FMMonth YYYY')
                            ELSE NULL
                        END
                    ), 'YYYY-MM') as latest_flight
                FROM reviews
                WHERE LOWER("airlineName") = LOWER(%s)
                    AND seatType IS NOT NULL 
                    AND route IS NOT NULL
                    AND dateReview IS NOT NULL
                    AND dateFlown IS NOT NULL;
                """,
                (airline_name,)
            )
            
            pref_row = self.cur.fetchone()
            
            return {
                "top_rated_item": top_rated_item,
                "total_rated_users": {
                    "count": airline_row[8],
                    "medium_number": median_score
                },
                "overall_score": {
                    "score": f"{round(airline_row[7], 1)} / 10" if airline_row[7] else "N/A",
                    "rank": f"{rank} out of {total_airlines} airlines"
                },
                "lowest_rated_item": lowest_rated_item,
                "preferred_seat_type": pref_row[0] if pref_row and pref_row[0] else "N/A",
                "preferred_route": pref_row[1] if pref_row and pref_row[1] else "N/A",
                "review_time": {
                    "start": pref_row[2].strftime("%Y-%m-%d") if pref_row and pref_row[2] else "N/A",
                    "end": pref_row[3].strftime("%Y-%m-%d") if pref_row and pref_row[3] else "N/A"
                },
                "flown_time": {
                    "start": pref_row[4] if pref_row and pref_row[4] else "N/A",
                    "end": pref_row[5] if pref_row and pref_row[5] else "N/A"
                }
            }
            
        except Exception as e:
            print(f"Error getting airline key data: {e}")
            return None

    def get_rating_distribution(self, airline_name):
        try:
            self.cur.execute(
                """
                SELECT 
                    COUNT(*) FILTER (WHERE seatComfort = 0) as seat_0,
                    COUNT(*) FILTER (WHERE seatComfort = 1) as seat_1,
                    COUNT(*) FILTER (WHERE seatComfort = 2) as seat_2,
                    COUNT(*) FILTER (WHERE seatComfort = 3) as seat_3,
                    COUNT(*) FILTER (WHERE seatComfort = 4) as seat_4,
                    COUNT(*) FILTER (WHERE seatComfort = 5) as seat_5,
                    
                    COUNT(*) FILTER (WHERE cabinStaffService = 0) as cabin_0,
                    COUNT(*) FILTER (WHERE cabinStaffService = 1) as cabin_1,
                    COUNT(*) FILTER (WHERE cabinStaffService = 2) as cabin_2,
                    COUNT(*) FILTER (WHERE cabinStaffService = 3) as cabin_3,
                    COUNT(*) FILTER (WHERE cabinStaffService = 4) as cabin_4,
                    COUNT(*) FILTER (WHERE cabinStaffService = 5) as cabin_5,
                    
                    COUNT(*) FILTER (WHERE foodBeverages = 0) as food_0,
                    COUNT(*) FILTER (WHERE foodBeverages = 1) as food_1,
                    COUNT(*) FILTER (WHERE foodBeverages = 2) as food_2,
                    COUNT(*) FILTER (WHERE foodBeverages = 3) as food_3,
                    COUNT(*) FILTER (WHERE foodBeverages = 4) as food_4,
                    COUNT(*) FILTER (WHERE foodBeverages = 5) as food_5,
                    
                    COUNT(*) FILTER (WHERE inflightEntertainment = 0) as entertainment_0,
                    COUNT(*) FILTER (WHERE inflightEntertainment = 1) as entertainment_1,
                    COUNT(*) FILTER (WHERE inflightEntertainment = 2) as entertainment_2,
                    COUNT(*) FILTER (WHERE inflightEntertainment = 3) as entertainment_3,
                    COUNT(*) FILTER (WHERE inflightEntertainment = 4) as entertainment_4,
                    COUNT(*) FILTER (WHERE inflightEntertainment = 5) as entertainment_5,
                    
                    COUNT(*) FILTER (WHERE groundService = 0) as ground_0,
                    COUNT(*) FILTER (WHERE groundService = 1) as ground_1,
                    COUNT(*) FILTER (WHERE groundService = 2) as ground_2,
                    COUNT(*) FILTER (WHERE groundService = 3) as ground_3,
                    COUNT(*) FILTER (WHERE groundService = 4) as ground_4,
                    COUNT(*) FILTER (WHERE groundService = 5) as ground_5,
                    
                    COUNT(*) FILTER (WHERE wifiConnectivity = 0) as wifi_0,
                    COUNT(*) FILTER (WHERE wifiConnectivity = 1) as wifi_1,
                    COUNT(*) FILTER (WHERE wifiConnectivity = 2) as wifi_2,
                    COUNT(*) FILTER (WHERE wifiConnectivity = 3) as wifi_3,
                    COUNT(*) FILTER (WHERE wifiConnectivity = 4) as wifi_4,
                    COUNT(*) FILTER (WHERE wifiConnectivity = 5) as wifi_5,
                    
                    COUNT(*) FILTER (WHERE valueForMoney = 0) as value_0,
                    COUNT(*) FILTER (WHERE valueForMoney = 1) as value_1,
                    COUNT(*) FILTER (WHERE valueForMoney = 2) as value_2,
                    COUNT(*) FILTER (WHERE valueForMoney = 3) as value_3,
                    COUNT(*) FILTER (WHERE valueForMoney = 4) as value_4,
                    COUNT(*) FILTER (WHERE valueForMoney = 5) as value_5
                FROM reviews
                WHERE LOWER("airlineName") = LOWER(%s);
                """,
                (airline_name,)
            )
            
            row = self.cur.fetchone()
            
            if not row:
                return None
            
            total_seat = sum(row[0:6])
            total_cabin = sum(row[6:12])
            total_food = sum(row[12:18])
            total_entertainment = sum(row[18:24])
            total_ground = sum(row[24:30])
            total_wifi = sum(row[30:36])
            total_value = sum(row[36:42])
            
            return {
                "Seat Comfort": [
                    row[i] / total_seat if total_seat > 0 else 0 
                    for i in range(0, 6)
                ],
                "Cabin & Staff Service": [
                    row[i] / total_cabin if total_cabin > 0 else 0 
                    for i in range(6, 12)
                ],
                "Food & Beverages": [
                    row[i] / total_food if total_food > 0 else 0 
                    for i in range(12, 18)
                ],
                "Inflight Entertainment": [
                    row[i] / total_entertainment if total_entertainment > 0 else 0 
                    for i in range(18, 24)
                ],
                "Ground Service": [
                    row[i] / total_ground if total_ground > 0 else 0 
                    for i in range(24, 30)
                ],
                "Wifi Connectivity": [
                    row[i] / total_wifi if total_wifi > 0 else 0 
                    for i in range(30, 36)
                ],
                "Value For Money": [
                    row[i] / total_value if total_value > 0 else 0 
                    for i in range(36, 42)
                ]
            }
            
        except Exception as e:
            print(f"Error getting rating distribution: {e}")
            return None

    def get_aspect_sentiment_scoring(self, airline_name, min_reviews=10):
        """
        Get aspect-based sentiment scoring (using sentiment pipeline results)
        
        Optimization: Use pre-processed sentiment_score, combine with keyword matching to assign aspects
        Avoid real-time model loading and analysis, significantly improve performance
        
        Args:
            airline_name: Airline name
            min_reviews: Minimum number of reviews
            
        Returns:
            Dictionary containing target airline and average aspect sentiment scores
        """
        try:
            # Define keywords for each aspect (for matching reviews)
            aspect_keywords = {
                'Seat Comfort': ['seat', 'sitting', 'comfortable', 'legroom', 'space', 'cushion', 'recline', 'width', 'padding', 'ergonomic', 'uncomfortable', 'cramped'],
                'Cabin Staff & Service': ['staff', 'crew', 'attendant', 'service', 'friendly', 'helpful', 'professional', 'courteous', 'polite', 'rude', 'unhelpful', 'smile'],
                'Food & Beverages': ['food', 'meal', 'dinner', 'lunch', 'breakfast', 'beverage', 'drink', 'taste', 'delicious', 'tasty', 'quality', 'menu', 'catering', 'snack'],
                'Inflight Entertainment': ['entertainment', 'movie', 'tv', 'screen', 'music', 'games', 'wifi', 'film', 'show', 'program', 'channel', 'selection', 'headphone'],
                'Ground Service': ['ground', 'check-in', 'boarding', 'gate', 'luggage', 'baggage', 'terminal', 'queue', 'wait', 'delay', 'efficient', 'slow'],
                'Wifi Connectivity': ['wifi', 'internet', 'connection', 'connectivity', 'network', 'signal', 'online', 'streaming', 'download', 'speed', 'free', 'paid'],
                'Value for Money': ['price', 'cost', 'value', 'money', 'expensive', 'cheap', 'worth', 'affordable', 'budget', 'pricing', 'fee', 'charge', 'reasonable']
            }
            
            # Get reviews and sentiment_score for this airline (pre-processed)
            self.cur.execute(
                """
                SELECT rc.cleaned_text, rs.sentiment_score
                FROM reviews_clean rc
                JOIN reviews_sentiment rs 
                    ON rc.review_id = rs.review_id 
                    AND LOWER(rc."airlineName") = LOWER(rs."airlineName")
                WHERE LOWER(rc."airlineName") = LOWER(%s)
                    AND rc.cleaned_text IS NOT NULL
                    AND rc.cleaned_text != ''
                    AND rs.sentiment_score IS NOT NULL
                LIMIT %s;
                """,
                (airline_name, min_reviews * 20)  # Get more reviews for better accuracy
            )
            
            reviews = self.cur.fetchall()
            
            if not reviews or len(reviews) < min_reviews:
                return None
            
            # Use keyword matching and pre-processed sentiment_score to assign aspects
            aspect_scores = {aspect: [] for aspect in aspect_keywords.keys()}
            
            for text, sentiment_score in reviews:
                text_lower = text.lower()
                # Check keyword matching for each aspect
                for aspect, keywords in aspect_keywords.items():
                    if any(keyword in text_lower for keyword in keywords):
                        # Convert sentiment_score (-1 to 1) to 0-5 scale
                        score_0_5 = (float(sentiment_score) + 1) / 2 * 5
                        aspect_scores[aspect].append(score_0_5)
            
            # Calculate average scores
            target_scores = {}
            for aspect, scores in aspect_scores.items():
                if scores:
                    target_scores[aspect] = round(sum(scores) / len(scores), 2)
                else:
                    target_scores[aspect] = 0.0
            
            # Get average aspect sentiment scores for all airlines
            self.cur.execute(
                """
                SELECT rc.cleaned_text, rs.sentiment_score
                FROM reviews_clean rc
                JOIN reviews_sentiment rs 
                    ON rc.review_id = rs.review_id 
                    AND LOWER(rc."airlineName") = LOWER(rs."airlineName")
                WHERE rc.cleaned_text IS NOT NULL
                    AND rc.cleaned_text != ''
                    AND rs.sentiment_score IS NOT NULL
                LIMIT 2000;
                """
            )
            
            all_reviews = self.cur.fetchall()
            all_aspect_scores = {aspect: [] for aspect in aspect_keywords.keys()}
            
            for text, sentiment_score in all_reviews:
                text_lower = text.lower()
                for aspect, keywords in aspect_keywords.items():
                    if any(keyword in text_lower for keyword in keywords):
                        score_0_5 = (float(sentiment_score) + 1) / 2 * 5
                        all_aspect_scores[aspect].append(score_0_5)
            
            avg_scores = {}
            for aspect, scores in all_aspect_scores.items():
                if scores:
                    avg_scores[aspect] = round(sum(scores) / len(scores), 2)
                else:
                    avg_scores[aspect] = 0.0
            
            # Convert to same format as get_sub_item_scoring
            return {
                "target_airline": {
                    "Seat Comfort": target_scores.get('Seat Comfort', 0) or 0,
                    "Cabin Staff & Service": target_scores.get('Cabin Staff & Service', 0) or 0,
                    "Food & Beverages": target_scores.get('Food & Beverages', 0) or 0,
                    "Inflight Entertainment": target_scores.get('Inflight Entertainment', 0) or 0,
                    "Ground Service": target_scores.get('Ground Service', 0) or 0,
                    "Wifi Connectivity": target_scores.get('Wifi Connectivity', 0) or 0,
                    "Value for Money": target_scores.get('Value for Money', 0) or 0
                },
                "average_score": {
                    "Seat Comfort": avg_scores.get('Seat Comfort', 0) or 0,
                    "Cabin Staff & Service": avg_scores.get('Cabin Staff & Service', 0) or 0,
                    "Food & Beverages": avg_scores.get('Food & Beverages', 0) or 0,
                    "Inflight Entertainment": avg_scores.get('Inflight Entertainment', 0) or 0,
                    "Ground Service": avg_scores.get('Ground Service', 0) or 0,
                    "Wifi Connectivity": avg_scores.get('Wifi Connectivity', 0) or 0,
                    "Value for Money": avg_scores.get('Value for Money', 0) or 0
                }
            }
            
        except Exception as e:
            print(f"Error getting aspect sentiment scoring: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_sub_item_scoring(self, airline_name):
        try:
            self.cur.execute(
                """
                SELECT 
                    "seatComfort",
                    "cabinStaffService",
                    "foodBeverages",
                    "inflightEntertainment",
                    "groundService",
                    "wifiConnectivity",
                    "valueForMoney"
                FROM airlines
                WHERE LOWER(name) = LOWER(%s);
                """,
                (airline_name,)
            )
            
            target_row = self.cur.fetchone()
            
            if not target_row:
                return None
            
            self.cur.execute(
                """
                SELECT 
                    SUM("seatComfort" * "calculatedReviewCount") / SUM("calculatedReviewCount") as avg_seatComfort,
                    SUM("cabinStaffService" * "calculatedReviewCount") / SUM("calculatedReviewCount") as avg_cabinStaffService,
                    SUM("foodBeverages" * "calculatedReviewCount") / SUM("calculatedReviewCount") as avg_foodBeverages,
                    SUM("inflightEntertainment" * "calculatedReviewCount") / SUM("calculatedReviewCount") as avg_inflightEntertainment,
                    SUM("groundService" * "calculatedReviewCount") / SUM("calculatedReviewCount") as avg_groundService,
                    SUM("wifiConnectivity" * "calculatedReviewCount") / SUM("calculatedReviewCount") as avg_wifiConnectivity,
                    SUM("valueForMoney" * "calculatedReviewCount") / SUM("calculatedReviewCount") as avg_valueForMoney
                FROM airlines
                WHERE "calculatedReviewCount" > 0
                AND "seatComfort" IS NOT NULL
                AND "cabinStaffService" IS NOT NULL
                AND "foodBeverages" IS NOT NULL
                AND "inflightEntertainment" IS NOT NULL
                AND "groundService" IS NOT NULL
                AND "wifiConnectivity" IS NOT NULL
                AND "valueForMoney" IS NOT NULL;
                """
            )
            
            avg_row = self.cur.fetchone()
            
            return {
                "target_airline": {
                    "Seat Comfort": round(target_row[0], 1) if target_row[0] is not None else 0,
                    "Cabin Staff & Service": round(target_row[1], 1) if target_row[1] is not None else 0,
                    "Food & Beverages": round(target_row[2], 1) if target_row[2] is not None else 0,
                    "Inflight Entertainment": round(target_row[3], 1) if target_row[3] is not None else 0,
                    "Ground Service": round(target_row[4], 1) if target_row[4] is not None else 0,
                    "Wifi Connectivity": round(target_row[5], 1) if target_row[5] is not None else 0,
                    "Value for Money": round(target_row[6], 1) if target_row[6] is not None else 0
                },
                "average_score": {
                    "Seat Comfort": round(avg_row[0], 1) if avg_row and avg_row[0] is not None else 0,
                    "Cabin Staff & Service": round(avg_row[1], 1) if avg_row and avg_row[1] is not None else 0,
                    "Food & Beverages": round(avg_row[2], 1) if avg_row and avg_row[2] is not None else 0,
                    "Inflight Entertainment": round(avg_row[3], 1) if avg_row and avg_row[3] is not None else 0,
                    "Ground Service": round(avg_row[4], 1) if avg_row and avg_row[4] is not None else 0,
                    "Wifi Connectivity": round(avg_row[5], 1) if avg_row and avg_row[5] is not None else 0,
                    "Value for Money": round(avg_row[6], 1) if avg_row and avg_row[6] is not None else 0
                }
            }
            
        except Exception as e:
            print(f"Error getting sub-item scoring: {e}")
            return None
    
    def get_top_rated_airlines(self, min_reviews=50, use_weighted_ranking=True):
        """
        Get top-rated airlines
        
        Args:
            min_reviews: Minimum review count threshold (default: 10)
            use_weighted_ranking: Whether to use weighted ranking (Bayesian average)
        
        Returns:
            List of airlines sorted by weighted score
        """
        try:
            # First get global average score (for Bayesian average)
            self.cur.execute(
                """
                SELECT AVG(score)
                FROM airlines
                WHERE score IS NOT NULL
                AND "calculatedReviewCount" IS NOT NULL
                AND "calculatedReviewCount" >= %s;
                """,
                (min_reviews,)
            )
            global_avg_result = self.cur.fetchone()
            global_avg_score = global_avg_result[0] if global_avg_result and global_avg_result[0] else 7.0
            
            # Get all airline data
            self.cur.execute(
                """
                SELECT 
                    name,
                    score,
                    "calculatedReviewCount"
                FROM airlines
                WHERE score IS NOT NULL
                AND "calculatedReviewCount" IS NOT NULL
                AND "calculatedReviewCount" >= %s;
                """,
                (min_reviews,)
            )
            
            results = self.cur.fetchall()
            
            if not results:
                return []

            # Calculate weighted score (Bayesian average)
            # Formula: (total_reviews * avg_score + C * global_avg) / (total_reviews + C)
            # C is a constant representing how many reviews needed to approach true average
            # Here we use min_reviews as C value
            C = min_reviews
            
            airlines_with_weighted_score = []
            for row in results:
                name, score, review_count = row
                
                if use_weighted_ranking:
                    # Bayesian average
                    weighted_score = (
                        (review_count * score + C * global_avg_score) / 
                        (review_count + C)
                    )
                else:
                    # No weighting, use raw score directly
                    weighted_score = score
                
                airlines_with_weighted_score.append({
                    "name": name,
                    "score": score,
                    "reviewCount": review_count,
                    "weightedScore": weighted_score
                })
            
            # Sort by weighted score
            airlines_with_weighted_score.sort(key=lambda x: x["weightedScore"], reverse=True)
            
            colors = ['#0095ff', '#00e096', '#884dff', '#ff8f0d', '#f64e60']
        
            return [
                {
                    "rank": str(i + 1).zfill(2),
                    "name": airline["name"],
                    "rating": round(airline["score"], 1),
                    "reviewCount": airline["reviewCount"],
                    "weightedRating": round(airline["weightedScore"], 2),  # Weighted score (for debugging)
                    "color": colors[i % len(colors)]
                }
                for i, airline in enumerate(airlines_with_weighted_score)
            ]
            
        except Exception as e:
            print(f"Error getting top rated airlines: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_airline_city_distribution(self, airline_name, cities_csv_path='worldcities.csv'):
        try:
            import csv
            city_coords = {}
            
            with open(cities_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    city_name = row['city']
                    city_coords[city_name] = {
                        'lng': float(row['lng']),
                        'lat': float(row['lat'])
                    }
            
            self.cur.execute(
                """
                SELECT 
                    route,
                    COUNT(*) as route_count
                FROM reviews
                WHERE LOWER("airlineName") = LOWER(%s)
                AND route IS NOT NULL
                AND route != ''
                AND route LIKE '%%to%%'
                GROUP BY route;
                """,
                (airline_name,)
            )
            
            results = self.cur.fetchall()

            if not results:
                return []
            
            city_counts = {}
            
            for row in results:
                route = row[0]
                count = row[1]
                
                if ' to ' in route:
                    parts = route.split(' to ')
                    if len(parts) == 2:
                        origin = parts[0].strip()
                        destination = parts[1].strip()
                        
                        city_counts[origin] = city_counts.get(origin, 0) + count
                        city_counts[destination] = city_counts.get(destination, 0) + count
            
            scatter_data = []
            colors = ['#fbbf24', '#ef4444', '#8b5cf6', '#06b6d4', '#10b981', '#22c55e']
            
            for i, (city, count) in enumerate(sorted(city_counts.items(), key=lambda x: x[1], reverse=True)):
                coords = city_coords.get(city)
                if coords:
                    scatter_data.append({
                        "name": city,
                        "value": [coords['lng'], coords['lat'], count],
                        "itemStyle": {"color": colors[i % len(colors)]}
                    })
            
            return scatter_data
            
        except Exception as e:
            print(f"Error getting city distribution: {e}")
            return []

    def get_airline_info(self, airline_name):
        try:
            self.cur.execute(
                """
                SELECT 
                    name,
                    image
                FROM airlines
                WHERE LOWER(name) = LOWER(%s);
                """,
                (airline_name,)
            )
            
            row = self.cur.fetchone()
            
            if not row:
                return None
            
            return {
                "name": row[0],
                "image": row[1] if row[1] else ""
            }
            
        except Exception as e:
            print(f"Error getting airline info: {e}")
            return None

    def search_reviews(
        self,
        airline_name: str,
        start_date: str = None,
        end_date: str = None,
        min_rating: int = None,
        max_rating: int = None,
        sentiment: str = None,  # 'pos', 'neg', 'neutral'
        topic_id: int = None,
        aspect: str = None,  # 'Seat Comfort', 'Cabin Staff & Service', etc.
        destination: str = None,
        page: int = 1,
        page_size: int = 20
    ):
        r"""
        Search reviews (supports multiple filter conditions and pagination)
        
        Args:
            airline_name: Airline name
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            min_rating: Minimum rating
            max_rating: Maximum rating
            sentiment: Sentiment ('pos', 'neg', 'neutral')
            topic_id: Topic ID
            aspect: Aspect name
            destination: Destination
            page: Page number (starts from 1)
            page_size: Items per page
            
        Returns:
            Dictionary containing reviews, total_count, page, page_size, summary
        """
        try:
            from datetime import datetime
            
            # Build WHERE conditions
            where_conditions = ['LOWER(r."airlineName") = LOWER(%s)']
            params = [airline_name]
            
            # Time range filter
            if start_date:
                where_conditions.append('r."dateReview" >= %s')
                params.append(start_date)
            if end_date:
                where_conditions.append('r."dateReview" <= %s')
                params.append(end_date)
            
            # Rating filter
            if min_rating is not None:
                where_conditions.append('r.score >= %s')
                params.append(min_rating)
            if max_rating is not None:
                where_conditions.append('r.score <= %s')
                params.append(max_rating)
            
            # Sentiment filter
            if sentiment:
                sentiment_map = {
                    'pos': 'Positive',
                    'neg': 'Negative',
                    'neutral': 'Neutral'
                }
                actual_sentiment = sentiment_map.get(sentiment, sentiment)
                where_conditions.append('rs.sentiment_label = %s')
                params.append(actual_sentiment)
            
            # Topic filter
            if topic_id is not None:
                where_conditions.append('rt.topic_id = %s')
                params.append(topic_id)
            
            # Aspect filter (via keyword matching)
            aspect_keywords = {
                'Seat Comfort': ['seat', 'sitting', 'comfortable', 'legroom', 'space', 'cushion'],
                'Cabin Staff & Service': ['staff', 'crew', 'attendant', 'service', 'friendly'],
                'Food & Beverages': ['food', 'meal', 'dinner', 'lunch', 'breakfast', 'beverage'],
                'Inflight Entertainment': ['entertainment', 'movie', 'tv', 'screen', 'music'],
                'Ground Service': ['ground', 'check-in', 'boarding', 'gate', 'luggage'],
                'Wifi Connectivity': ['wifi', 'internet', 'connection', 'connectivity'],
                'Value for Money': ['price', 'cost', 'value', 'money', 'expensive']
            }
            
            if aspect and aspect in aspect_keywords:
                keywords = aspect_keywords[aspect]
                keyword_conditions = ' OR '.join(['LOWER(rc.cleaned_text) LIKE %s' for _ in keywords])
                where_conditions.append(f'({keyword_conditions})')
                params.extend([f'%{kw}%' for kw in keywords])
            
            # Destination filter
            if destination:
                where_conditions.append('LOWER(r.route) LIKE %s')
                params.append(f'%{destination.lower()}%')
            
            where_clause = ' AND '.join(where_conditions)
            
            # Calculate total count
            count_query = f"""
                SELECT COUNT(DISTINCT r."reviewId")
                FROM reviews r
                LEFT JOIN reviews_clean rc ON r."reviewId" = rc.review_id
                LEFT JOIN reviews_sentiment rs ON r."reviewId" = rs.review_id AND LOWER(r."airlineName") = LOWER(rs."airlineName")
                LEFT JOIN reviews_topics rt ON r."reviewId" = rt.review_id
                WHERE {where_clause}
            """
            self.cur.execute(count_query, params)
            total_count = self.cur.fetchone()[0]
            
            # Get review data (paginated)
            offset = (page - 1) * page_size
            query = f"""
                SELECT DISTINCT
                    r."reviewId",
                    r.title,
                    r.score,
                    r.content,
                    r."verifiedType",
                    r."userName",
                    r.country,
                    r."dateReview",
                    r.aircraft,
                    r."typeOfTraveller",
                    r."seatType",
                    r."dateFlown",
                    r.recommended,
                    r.route,
                    rs.sentiment_label,
                    rs.sentiment_score,
                    rt.topic_id,
                    t.human_label as topic_label,
                    t.top_words as topic_words
                FROM reviews r
                LEFT JOIN reviews_clean rc ON r."reviewId" = rc.review_id
                LEFT JOIN reviews_sentiment rs ON r."reviewId" = rs.review_id AND LOWER(r."airlineName") = LOWER(rs."airlineName")
                LEFT JOIN reviews_topics rt ON r."reviewId" = rt.review_id AND rt.sentiment_bucket = rs.sentiment_label
                LEFT JOIN topics t ON rt.topic_id = t.topic_id AND rt.sentiment_bucket = t.sentiment_bucket
                WHERE {where_clause}
                ORDER BY r."dateReview" DESC
                LIMIT %s OFFSET %s
            """
            self.cur.execute(query, params + [page_size, offset])
            results = self.cur.fetchall()
            
            # Process results
            reviews = []
            for row in results:
                review_id, title, score, content, verified_type, user_name, country, date_review, aircraft, type_of_traveller, seat_type, date_flown, recommended, route, sentiment_label, sentiment_score, topic_id, topic_label, topic_words = row
                
                # Extract aspect keywords (for highlighting)
                matched_aspects = []
                if content:
                    content_lower = content.lower()
                    for asp, keywords in aspect_keywords.items():
                        if any(kw in content_lower for kw in keywords):
                            matched_aspects.append(asp)
                
                # Process dates (may be datetime objects or strings)
                def format_date(date_val):
                    if not date_val:
                        return ''
                    if isinstance(date_val, str):
                        return date_val
                    if hasattr(date_val, 'strftime'):
                        return date_val.strftime('%Y-%m-%d')
                    return str(date_val)
                
                reviews.append({
                    'reviewId': review_id,
                    'title': title or '',
                    'score': float(score) if score else None,
                    'content': content or '',
                    'verifiedType': verified_type or '',
                    'userName': user_name or '',
                    'country': country or '',
                    'reviewDate': format_date(date_review),
                    'aircraft': aircraft or '',
                    'typeOfTraveller': type_of_traveller or '',
                    'seatType': seat_type or '',
                    'flownDate': format_date(date_flown),
                    'recommended': recommended or '',
                    'route': route or '',
                    'sentiment_label': sentiment_label,
                    'sentiment_score': float(sentiment_score) if sentiment_score else None,
                    'topic_id': int(topic_id) if topic_id else None,
                    'topic_label': topic_label,
                    'topic_words': topic_words if isinstance(topic_words, list) else list(topic_words) if topic_words else [],
                    'matched_aspects': matched_aspects
                })
            
            # Calculate aggregated summary
            summary_query = f"""
                SELECT 
                    COUNT(DISTINCT r."reviewId") as count,
                    AVG(r.score) as avg_rating
                FROM reviews r
                LEFT JOIN reviews_clean rc ON r."reviewId" = rc.review_id
                LEFT JOIN reviews_sentiment rs ON r."reviewId" = rs.review_id AND LOWER(r."airlineName") = LOWER(rs."airlineName")
                LEFT JOIN reviews_topics rt ON r."reviewId" = rt.review_id
                WHERE {where_clause}
            """
            self.cur.execute(summary_query, params)
            summary_row = self.cur.fetchone()
            count = summary_row[0] if summary_row else 0
            avg_rating = float(summary_row[1]) if summary_row and summary_row[1] else None
            
            # Get Top Topics
            # Need to build separate WHERE conditions for top_topics query (no sentiment filter, as topics table is already grouped by sentiment_bucket)
            top_topics_where_conditions = ['LOWER(r."airlineName") = LOWER(%s)']
            top_topics_params = [airline_name]
            
            if start_date:
                top_topics_where_conditions.append('r."dateReview" >= %s')
                top_topics_params.append(start_date)
            if end_date:
                top_topics_where_conditions.append('r."dateReview" <= %s')
                top_topics_params.append(end_date)
            if min_rating is not None:
                top_topics_where_conditions.append('r.score >= %s')
                top_topics_params.append(min_rating)
            if max_rating is not None:
                top_topics_where_conditions.append('r.score <= %s')
                top_topics_params.append(max_rating)
            if topic_id is not None:
                top_topics_where_conditions.append('rt.topic_id = %s')
                top_topics_params.append(topic_id)
            if destination:
                top_topics_where_conditions.append('LOWER(r.route) LIKE %s')
                top_topics_params.append(f'%{destination.lower()}%')
            
            top_topics_where_clause = ' AND '.join(top_topics_where_conditions)
            
            top_topics_query = f"""
                SELECT 
                    rt.topic_id,
                    t.human_label,
                    COUNT(*) as review_count
                FROM reviews r
                LEFT JOIN reviews_topics rt ON r."reviewId" = rt.review_id
                LEFT JOIN topics t ON rt.topic_id = t.topic_id AND rt.sentiment_bucket = t.sentiment_bucket
                WHERE {top_topics_where_clause}
                    AND rt.topic_id IS NOT NULL
                GROUP BY rt.topic_id, t.human_label
                ORDER BY review_count DESC
                LIMIT 5
            """
            self.cur.execute(top_topics_query, top_topics_params)
            top_topics = [
                {'topic_id': int(row[0]), 'label': row[1], 'count': int(row[2])}
                for row in self.cur.fetchall()
            ]
            
            # Get Top Aspects
            # Need to build separate WHERE conditions for top_aspects query
            top_aspects_where_conditions = ['LOWER(r."airlineName") = LOWER(%s)']
            top_aspects_params = [airline_name]
            
            if start_date:
                top_aspects_where_conditions.append('r."dateReview" >= %s')
                top_aspects_params.append(start_date)
            if end_date:
                top_aspects_where_conditions.append('r."dateReview" <= %s')
                top_aspects_params.append(end_date)
            if min_rating is not None:
                top_aspects_where_conditions.append('r.score >= %s')
                top_aspects_params.append(min_rating)
            if max_rating is not None:
                top_aspects_where_conditions.append('r.score <= %s')
                top_aspects_params.append(max_rating)
            if sentiment:
                sentiment_map = {
                    'pos': 'Positive',
                    'neg': 'Negative',
                    'neutral': 'Neutral'
                }
                actual_sentiment = sentiment_map.get(sentiment, sentiment)
                top_aspects_where_conditions.append('rs.sentiment_label = %s')
                top_aspects_params.append(actual_sentiment)
            if topic_id is not None:
                top_aspects_where_conditions.append('rt.topic_id = %s')
                top_aspects_params.append(topic_id)
            if destination:
                top_aspects_where_conditions.append('LOWER(r.route) LIKE %s')
                top_aspects_params.append(f'%{destination.lower()}%')
            
            top_aspects_where_clause = ' AND '.join(top_aspects_where_conditions)
            
            top_aspects = []
            for aspect_name, keywords in aspect_keywords.items():
                aspect_count_query = f"""
                    SELECT COUNT(DISTINCT r."reviewId")
                    FROM reviews r
                    LEFT JOIN reviews_clean rc ON r."reviewId" = rc.review_id
                    LEFT JOIN reviews_sentiment rs ON r."reviewId" = rs.review_id
                    LEFT JOIN reviews_topics rt ON r."reviewId" = rt.review_id
                    WHERE {top_aspects_where_clause}
                        AND ({' OR '.join(['LOWER(rc.cleaned_text) LIKE %s' for _ in keywords])})
                """
                self.cur.execute(aspect_count_query, top_aspects_params + [f'%{kw}%' for kw in keywords])
                aspect_count = self.cur.fetchone()[0]
                if aspect_count > 0:
                    top_aspects.append({
                        'aspect': aspect_name,
                        'count': aspect_count
                    })
            top_aspects.sort(key=lambda x: x['count'], reverse=True)
            top_aspects = top_aspects[:5]
            
            return {
                'reviews': reviews,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': (total_count + page_size - 1) // page_size
                },
                'summary': {
                    'count': count,
                    'avg_rating': avg_rating,
                    'top_topics': top_topics,
                    'top_aspects': top_aspects
                }
            }
            
        except Exception as e:
            print(f"Error searching reviews: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def compute_topic_drivers(
        self, 
        airline_name: str, 
        start_date: str = None,
        end_date: str = None,
        min_samples: int = 30,
        model_spec: str = 'default'
    ):
        """
        Compute topic drivers (run OLS regression analysis, normalize topic_score to shares)
        
        Args:
            airline_name: Airline name
            start_date: Start date (optional)
            end_date: End date (optional)
            min_samples: Minimum number of samples
            model_spec: Model specification identifier
            
        Returns:
            Analysis results
        """
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from topic_driver_analyzer import TopicDriverAnalyzer
            
            # Build WHERE conditions
            where_conditions = ['LOWER(r."airlineName") = LOWER(%s)', 'r.score IS NOT NULL', 'r.score > 0']
            params = [airline_name]
            
            if start_date:
                where_conditions.append('r."dateReview" >= %s')
                params.append(start_date)
            if end_date:
                where_conditions.append('r."dateReview" <= %s')
                params.append(end_date)
            
            where_clause = ' AND '.join(where_conditions)
            
            # Get reviews and ratings for this airline
            self.cur.execute(
                f"""
                SELECT r."reviewId", r.score
                FROM reviews r
                WHERE {where_clause}
                """,
                tuple(params)
            )
            ratings_data = self.cur.fetchall()
            
            if len(ratings_data) < min_samples:
                print(f"⚠️  Insufficient samples for OLS regression: {len(ratings_data)} reviews < {min_samples} required")
                print(f"   Note: OLS needs REVIEWS (not topics) - need at least {min_samples} reviews with both rating and topic data")
                print(f"   Current: {len(ratings_data)} reviews with ratings")
                return None
            
            # Get topic data for this airline (using topic_score, will be normalized to shares later)
            topic_where_conditions = ['LOWER(rt."airlineName") = LOWER(%s)']
            topic_params = [airline_name]
            
            if start_date:
                topic_where_conditions.append('r."dateReview" >= %s')
                topic_params.append(start_date)
            if end_date:
                topic_where_conditions.append('r."dateReview" <= %s')
                topic_params.append(end_date)
            
            topic_where_clause = ' AND '.join(topic_where_conditions)
            
            self.cur.execute(
                f"""
                SELECT rt.review_id, rt.topic_id, rt.topic_score
                FROM reviews_topics rt
                JOIN reviews r ON rt.review_id = r."reviewId"
                WHERE {topic_where_clause}
                """,
                tuple(topic_params)
            )
            topics_data = self.cur.fetchall()
            
            if not topics_data:
                print(f"⚠️  No topic data found for {airline_name}")
                return None
            
            # Check how many unique reviews have topic data
            unique_reviews_with_topics = len(set(row[0] for row in topics_data))
            if unique_reviews_with_topics < min_samples:
                print(f"⚠️  Insufficient reviews with topic data: {unique_reviews_with_topics} reviews < {min_samples} required")
                print(f"   Note: Need at least {min_samples} reviews that have BOTH rating and topic data")
                print(f"   Current: {unique_reviews_with_topics} reviews with topics, {len(ratings_data)} reviews with ratings")
                return None
            
            # Run analysis (will automatically normalize topic_score to shares)
            try:
                analyzer = TopicDriverAnalyzer()
                results = analyzer.analyze_topic_drivers(
                    topics_data,
                    ratings_data,
                    min_samples=min_samples
                )
            except ValueError as e:
                # Insufficient data or other validation errors
                print(f"⚠️  Analysis failed: {e}")
                return None
            except Exception as e:
                # Other analysis errors
                print(f"❌ Error during analysis: {e}")
                import traceback
                traceback.print_exc()
                return None
            
            # Save results to database
            from datetime import datetime
            created_at = datetime.now()
            
            for feature_name in results['feature_names']:
                topic_id = results['topic_id_map'][feature_name]
                coef = results['coefficients'][feature_name]
                se = results['std_errors'][feature_name]
                pval = results['p_values'][feature_name]
                ci_low = results['ci_low'][feature_name]
                ci_high = results['ci_high'][feature_name]
                
                self.cur.execute(
                    """
                    INSERT INTO topic_driver_results (
                        "airlineName", model_spec, topic_id, coef, se, pval,
                        ci_low, ci_high, n, r2, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT ("airlineName", model_spec, topic_id, created_at) DO UPDATE SET
                        coef = EXCLUDED.coef,
                        se = EXCLUDED.se,
                        pval = EXCLUDED.pval,
                        ci_low = EXCLUDED.ci_low,
                        ci_high = EXCLUDED.ci_high,
                        n = EXCLUDED.n,
                        r2 = EXCLUDED.r2;
                    """,
                    (
                        airline_name, model_spec, topic_id, coef, se, pval,
                        ci_low, ci_high, results['sample_size'], results['r_squared'], created_at
                    )
                )
            
            self.conn.commit()
            
            # Get topic labels
            topic_ids = [results['topic_id_map'][name] for name in results['feature_names']]
            self.cur.execute(
                """
                SELECT topic_id, human_label, top_words
                FROM topics
                WHERE topic_id = ANY(%s)
                """,
                (topic_ids,)
            )
            topic_info = {row[0]: {'label': row[1], 'words': row[2]} for row in self.cur.fetchall()}
            
            # Return formatted results
            topics = []
            for feature_name in results['feature_names']:
                topic_id = results['topic_id_map'][feature_name]
                info = topic_info.get(topic_id, {'label': f'Topic {topic_id}', 'words': []})
                topics.append({
                    'topic_id': topic_id,
                    'topic_label': info['label'],
                    'top_words': info['words'] if isinstance(info['words'], list) else list(info['words']) if info['words'] else [],
                    'coef': results['coefficients'][feature_name],
                    'se': results['std_errors'][feature_name],
                    'p_value': results['p_values'][feature_name],
                    'ci_low': results['ci_low'][feature_name],
                    'ci_high': results['ci_high'][feature_name],
                })
            
            return {
                'topics': topics,
                'model_r_squared': results['r_squared'],
                'sample_size': results['sample_size'],
                'model_spec': model_spec
            }
            
        except Exception as e:
            print(f"Error computing topic drivers: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_topic_drivers(
        self, 
        airline_name: str, 
        model_spec: str = 'default',
        use_cached: bool = True
    ):
        """
        Get topic drivers results
        
        Args:
            airline_name: Airline name
            model_spec: Model specification identifier
            use_cached: Whether to use cached (latest) results
            
        Returns:
            Topic drivers results
        """
        try:
            if use_cached:
                # Get latest results
                self.cur.execute(
                    """
                    SELECT 
                        tdr.topic_id,
                        t.human_label,
                        t.top_words,
                        tdr.coef,
                        tdr.se,
                        tdr.pval,
                        tdr.ci_low,
                        tdr.ci_high,
                        tdr.n,
                        tdr.r2
                    FROM topic_driver_results tdr
                    LEFT JOIN topics t ON tdr.topic_id = t.topic_id
                    WHERE LOWER(tdr."airlineName") = LOWER(%s)
                        AND tdr.model_spec = %s
                        AND tdr.created_at = (
                            SELECT MAX(created_at)
                            FROM topic_driver_results
                            WHERE LOWER("airlineName") = LOWER(%s)
                                AND model_spec = %s
                        )
                    ORDER BY ABS(tdr.coef) DESC
                    """,
                    (airline_name, model_spec, airline_name, model_spec)
                )
                
                results = self.cur.fetchall()
                
                if results:
                    topics = []
                    model_r_squared = None
                    sample_size = None
                    
                    for row in results:
                        topic_id, label, words, coef, se, pval, ci_low, ci_high, n, r2 = row
                        topics.append({
                            'topic_id': int(topic_id),
                            'topic_label': label or f'Topic {topic_id}',
                            'top_words': words if isinstance(words, list) else list(words) if words else [],
                            'coef': float(coef),
                            'se': float(se),
                            'p_value': float(pval),
                            'ci_low': float(ci_low),
                            'ci_high': float(ci_high),
                        })
                        if model_r_squared is None:
                            model_r_squared = float(r2)
                            sample_size = int(n)
                    
                    return {
                        'topics': topics,
                        'model_r_squared': model_r_squared,
                        'sample_size': sample_size,
                        'model_spec': model_spec
                    }
            
            return None
            
        except Exception as e:
            print(f"Error getting topic drivers: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def simulate_rating_change(
        self,
        airline_name: str,
        topic_changes: List[Dict],  # [{'topic_id': int, 'share_change_pct': float}, ...]
        start_date: str = None,
        end_date: str = None
    ):
        """
        Simulate the impact of topic share changes on rating
        
        Args:
            airline_name: Airline name
            topic_changes: List of topic changes, each element contains topic_id and share_change_pct (change percentage, -50 to +50)
                          - Negative value means decrease share (for negative topics)
                          - Positive value means increase share (for positive topics)
            start_date: Start date (optional)
            end_date: End date (optional)
            
        Returns:
            Simulation results, including predicted rating changes and uncertainty intervals
        """
        try:
            # Get current topic drivers
            model_spec = 'default'
            if start_date or end_date:
                model_spec = f"range_{start_date or 'all'}_{end_date or 'all'}"
            
            drivers = self.get_topic_drivers(airline_name, model_spec, use_cached=True)
            
            if not drivers:
                # If no cache, compute once
                drivers = self.compute_topic_drivers(airline_name, start_date, end_date, model_spec=model_spec)
            
            if not drivers:
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
                
                self.cur.execute(
                    f"""
                    SELECT COUNT(DISTINCT rt.review_id)
                    FROM reviews_topics rt
                    JOIN reviews r ON rt.review_id = r."reviewId"
                    WHERE {topic_check_clause}
                    """,
                    tuple(topic_check_params)
                )
                topic_count = self.cur.fetchone()[0]
                
                if topic_count == 0:
                    date_range_str = f" ({start_date} to {end_date})" if (start_date or end_date) else ""
                    raise ValueError(
                        f"No topic data available for {airline_name}{date_range_str}. "
                        f"Please run topic mining pipeline or use a different date range. "
                        f"Tip: Check which date ranges have topic data available."
                    )
                else:
                    raise ValueError(
                        f"Insufficient topic data for {airline_name} in the specified date range. "
                        f"Found {topic_count} reviews with topics, but need at least 30 for OLS regression."
                    )
            
            # Get current average rating
            where_conditions = ['LOWER(r."airlineName") = LOWER(%s)', 'r.score IS NOT NULL']
            params = [airline_name]
            
            if start_date:
                where_conditions.append('r."dateReview" >= %s')
                params.append(start_date)
            if end_date:
                where_conditions.append('r."dateReview" <= %s')
                params.append(end_date)
            
            where_clause = ' AND '.join(where_conditions)
            
            self.cur.execute(
                f"""
                SELECT AVG(r.score)
                FROM reviews r
                WHERE {where_clause}
                """,
                tuple(params)
            )
            current_avg_rating = self.cur.fetchone()[0]
            
            if not current_avg_rating:
                return None
            
            # Build topic_id to coefficient mapping
            topic_coef_map = {t['topic_id']: t for t in drivers['topics']}
            
            # Calculate predicted rating change
            total_delta_rating = 0.0
            topic_impacts = []
            priority_rankings = []
            
            for change in topic_changes:
                topic_id = change['topic_id']
                share_change_pct = change.get('share_change_pct', change.get('share_reduction_pct', 0))  # Support both old and new field names
                share_change = share_change_pct / 100.0  # Convert to decimal (-0.5 to +0.5)
                
                if topic_id not in topic_coef_map:
                    continue
                
                topic_info = topic_coef_map[topic_id]
                coef = topic_info['coef']
                ci_low = topic_info['ci_low']
                ci_high = topic_info['ci_high']
                
                # Calculate rating change
                # delta_rating = coef * share_change
                # - If coef < 0 (negative topic) and share_change < 0 (decrease), delta_rating > 0 (improve rating)
                # - If coef > 0 (positive topic) and share_change > 0 (increase), delta_rating > 0 (improve rating)
                delta_rating = coef * share_change
                
                # Calculate uncertainty interval
                if share_change > 0:
                    # Increase share
                    delta_rating_low = ci_low * share_change
                    delta_rating_high = ci_high * share_change
                else:
                    # Decrease share
                    delta_rating_low = ci_high * share_change
                    delta_rating_high = ci_low * share_change
                
                total_delta_rating += delta_rating
                
                # ROI = delta_rating / abs(share_change_pct) (rating change per 1% share change)
                roi = delta_rating / abs(share_change_pct) if share_change_pct != 0 else 0
                
                topic_impacts.append({
                    'topic_id': topic_id,
                    'topic_label': topic_info['topic_label'],
                    'share_change_pct': share_change_pct,
                    'delta_rating': delta_rating,
                    'delta_rating_low': delta_rating_low,
                    'delta_rating_high': delta_rating_high,
                    'coef': coef,
                    'roi': roi
                })
                
                priority_rankings.append({
                    'topic_id': topic_id,
                    'topic_label': topic_info['topic_label'],
                    'roi': roi,
                    'delta_rating': delta_rating
                })
            
            # Sort by ROI (descending)
            priority_rankings.sort(key=lambda x: x['roi'], reverse=True)
            
            # Calculate total uncertainty interval (simple addition, should consider correlation in practice)
            total_delta_low = sum(imp['delta_rating_low'] for imp in topic_impacts)
            total_delta_high = sum(imp['delta_rating_high'] for imp in topic_impacts)
            
            return {
                'current_avg_rating': float(current_avg_rating),
                'predicted_avg_rating': float(current_avg_rating) + total_delta_rating,
                'delta_rating': total_delta_rating,
                'delta_rating_low': total_delta_low,
                'delta_rating_high': total_delta_high,
                'topic_impacts': topic_impacts,
                'priority_rankings': priority_rankings,
                'model_r_squared': drivers['model_r_squared'],
                'sample_size': drivers['sample_size']
            }
            
        except ValueError:
            # Re-raise ValueError for caller to handle
            raise
        except Exception as e:
            print(f"Error simulating rating change: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_reviews_by_airline(self, airline_name, keyword=None):
        try:
            self.cur.execute(
                """
                SELECT 
                    "reviewId", title, score, content, "verifiedType", "userName", country,
                    "dateReview", aircraft, "typeOfTraveller", "seatType", "dateFlown", recommended
                FROM reviews
                WHERE LOWER("airlineName") = LOWER(%s)
                ORDER BY "dateReview" DESC;
                """,
                (airline_name,)
            )
            
            results = self.cur.fetchall()
            
            if not results:
                return []
            
            return [
                {
                    "reviewId": row[0] or "N/A",
                    "title": row[1] or "",
                    "score": round(row[2], 1) if row[2] is not None else 0,
                    "content": row[3] or "N/A",
                    "verifiedType": row[4] or "N/A",
                    "userName": row[5] or "N/A",
                    "country": row[6] or "N/A",
                    "reviewDate": row[7].strftime("%Y-%m-%d") if row[7] else "N/A",
                    "aircraft": row[8] or "N/A",
                    "typeOfTraveller": row[9] or "N/A",
                    "seatType": row[10] or "N/A",
                    "flownDate": row[11] or "N/A",
                    "recommended": row[12] or "N/A",
                }
                for row in results
            ]
            
        except Exception as e:
            print(f"Error getting reviews: {e}")
            return []

    def insert_sentiment(self, text, submit_time, sent_lab, pos_dict, neg_dict):
        try:
            self.cur.execute(
                """
                INSERT INTO sentiment (
                    text, submit_time, sent_lab, pos_dict, neg_dict
                ) VALUES (
                    %s, %s, %s, %s::jsonb, %s::jsonb
                );
                """, (text, submit_time, sent_lab, json.dumps(pos_dict), json.dumps(neg_dict))
            )
            
            self.conn.commit()
            
        except Exception as e:
            print(f"Error inserting sentiment: {e}")
            self.conn.rollback()

    def get_random_reviews(self, airline_name, limit=10):
        try:
            self.cur.execute(
                """
                SELECT content
                FROM reviews
                WHERE LOWER("airlineName") = LOWER(%s) AND content IS NOT NULL
                ORDER BY RANDOM()
                LIMIT %s;
                """,
                (airline_name, limit)
            )
            results = self.cur.fetchall()
            return [{'content': row[0]} for row in results]
        except Exception as e:
            print(f"Error getting random reviews: {e}")
            return []

    def get_topic_importance(self, airline_name: str, use_cached: bool = True):
        """
        Get topic importance analysis results
        
        Args:
            airline_name: Airline name
            use_cached: Whether to use cached results (from topic_importance table)
            
        Returns:
            Topic importance data, including coefficients, confidence intervals, etc.
        """
        try:
            if use_cached:
                # Try to get latest results from topic_importance table
                self.cur.execute(
                    """
                    SELECT 
                        topic_id,
                        topic_label,
                        coef,
                        p_value,
                        ci_low,
                        ci_high,
                        mean_topic_share,
                        model_r_squared,
                        sample_size
                    FROM topic_importance
                    WHERE LOWER("airlineName") = LOWER(%s)
                    ORDER BY created_at DESC
                    LIMIT 1;
                    """,
                    (airline_name,)
                )
                latest_result = self.cur.fetchone()
                
                if latest_result:
                    # Get all topics for this airline
                    self.cur.execute(
                        """
                        SELECT 
                            topic_id,
                            topic_label,
                            coef,
                            p_value,
                            ci_low,
                            ci_high,
                            mean_topic_share
                        FROM topic_importance
                        WHERE LOWER("airlineName") = LOWER(%s)
                            AND created_at = (
                                SELECT MAX(created_at) 
                                FROM topic_importance 
                                WHERE LOWER("airlineName") = LOWER(%s)
                            )
                        ORDER BY ABS(coef) DESC;
                        """,
                        (airline_name, airline_name)
                    )
                    
                    topics = []
                    r_squared = None
                    sample_size = None
                    
                    for row in self.cur.fetchall():
                        topic_id, topic_label, coef, p_value, ci_low, ci_high, mean_share = row
                        if r_squared is None:
                            # Get model statistics from first record
                            r_squared = latest_result[7]
                            sample_size = latest_result[8]
                        
                        topics.append({
                            'topic_id': int(topic_id),
                            'topic_label': topic_label or f'Topic {topic_id}',
                            'coef': float(coef) if coef else 0.0,
                            'p_value': float(p_value) if p_value else 1.0,
                            'ci_low': float(ci_low) if ci_low else 0.0,
                            'ci_high': float(ci_high) if ci_high else 0.0,
                            'mean_topic_share': float(mean_share) if mean_share else 0.0
                        })
                    
                    if topics:
                        return {
                            'topics': topics,
                            'model_r_squared': float(r_squared) if r_squared else None,
                            'sample_size': int(sample_size) if sample_size else None
                        }
            
            # If no cached results, return None (need to run analysis first)
            return None
            
        except Exception as e:
            print(f"Error getting topic importance: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def compute_topic_importance(self, airline_name: str, min_samples: int = 30):
        """
        Compute topic importance (run OLS regression analysis)
        
        Args:
            airline_name: Airline name
            min_samples: Minimum number of samples
            
        Returns:
            Analysis results
        """
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from topic_importance_analyzer import TopicImportanceAnalyzer
            
            # Get reviews and ratings for this airline
            self.cur.execute(
                """
                SELECT r."reviewId", r.score
                FROM reviews r
                WHERE LOWER(r."airlineName") = LOWER(%s)
                    AND r.score IS NOT NULL
                    AND r.score > 0;
                """,
                (airline_name,)
            )
            ratings_data = self.cur.fetchall()
            
            if len(ratings_data) < min_samples:
                return None
            
            # Get topic data for this airline
            self.cur.execute(
                """
                SELECT review_id, topic_id, topic_share
                FROM reviews_topics
                WHERE LOWER("airlineName") = LOWER(%s);
                """,
                (airline_name,)
            )
            topics_data = self.cur.fetchall()
            
            if not topics_data:
                return None
            
            # Run analysis
            analyzer = TopicImportanceAnalyzer()
            results = analyzer.analyze_topic_importance(
                topics_data,
                ratings_data,
                min_samples=min_samples
            )
            
            # Save results to database
            from datetime import datetime
            created_at = datetime.now()
            for feature_name in results['feature_names']:
                topic_id = int(feature_name.replace('topic_', ''))
                coef = results['coefficients'][feature_name]
                std_err = results['std_errors'][feature_name]
                p_value = results['p_values'][feature_name]
                ci_low = results['ci_low'][feature_name]
                ci_high = results['ci_high'][feature_name]
                mean_share = results['mean_topic_shares'].get(feature_name, 0.0)
                
                self.cur.execute(
                    """
                    INSERT INTO topic_importance (
                        "airlineName", topic_id, topic_label, coef, std_err, p_value,
                        ci_low, ci_high, mean_topic_share, model_r_squared, sample_size, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT ("airlineName", topic_id, created_at) DO UPDATE SET
                        coef = EXCLUDED.coef,
                        std_err = EXCLUDED.std_err,
                        p_value = EXCLUDED.p_value,
                        ci_low = EXCLUDED.ci_low,
                        ci_high = EXCLUDED.ci_high,
                        mean_topic_share = EXCLUDED.mean_topic_share,
                        model_r_squared = EXCLUDED.model_r_squared,
                        sample_size = EXCLUDED.sample_size;
                    """,
                    (
                        airline_name, topic_id, f'Topic {topic_id}',
                        coef, std_err, p_value, ci_low, ci_high, mean_share,
                        results['r_squared'], results['sample_size'], created_at
                    )
                )
            
            self.conn.commit()
            
            # Return formatted results
            topics = []
            for feature_name in results['feature_names']:
                topic_id = int(feature_name.replace('topic_', ''))
                topics.append({
                    'topic_id': topic_id,
                    'topic_label': f'Topic {topic_id}',
                    'coef': results['coefficients'][feature_name],
                    'p_value': results['p_values'][feature_name],
                    'ci_low': results['ci_low'][feature_name],
                    'ci_high': results['ci_high'][feature_name],
                    'mean_topic_share': results['mean_topic_shares'].get(feature_name, 0.0)
                })
            
            # Sort by absolute value
            topics.sort(key=lambda x: abs(x['coef']), reverse=True)
            
            return {
                'topics': topics,
                'model_r_squared': results['r_squared'],
                'sample_size': results['sample_size']
            }
            
        except Exception as e:
            print(f"Error computing topic importance: {e}")
            import traceback
            traceback.print_exc()
            self.conn.rollback()
            return None
    
    def get_reviews_for_regression(self, airline_name):
        try:
            self.cur.execute(
                """
                SELECT score, "seatComfort", "cabinStaffService", "foodBeverages",
                    "inflightEntertainment", "groundService", "wifiConnectivity", "valueForMoney"
                FROM reviews
                WHERE LOWER("airlineName") = LOWER(%s)
                AND score IS NOT NULL
                AND ("seatComfort" IS NOT NULL OR "cabinStaffService" IS NOT NULL 
                    OR "foodBeverages" IS NOT NULL OR "inflightEntertainment" IS NOT NULL
                    OR "groundService" IS NOT NULL OR "wifiConnectivity" IS NOT NULL
                    OR "valueForMoney" IS NOT NULL);
                """,
                (airline_name,)
            )
            results = self.cur.fetchall()
            return [
                {
                    'score': row[0],
                    'seatComfort': row[1],
                    'cabinStaffService': row[2],
                    'foodBeverages': row[3],
                    'inflightEntertainment': row[4],
                    'groundService': row[5],
                    'wifiConnectivity': row[6],
                    'valueForMoney': row[7]
                }
                for row in results
            ]
        except Exception as e:
            print(f"Error getting reviews for regression: {e}")
            return []
        
    def get_airline_kpis(self, airline_name, start_date=None, end_date=None, destination=None):
        """Get KPI metrics for an airline with optional date range and destination filter"""
        try:
            # Build WHERE clause
            conditions = ['LOWER("airlineName") = LOWER(%s)']
            params = [airline_name]
            
            if start_date:
                conditions.append('"dateReview" >= %s')
                params.append(start_date)
            
            if end_date:
                conditions.append('"dateReview" <= %s')
                params.append(end_date)
            
            if destination:
                conditions.append('(route LIKE %s OR route LIKE %s)')
                params.append(f'%{destination}%')
                params.append(f'%to {destination}%')
            
            where_clause = ' AND '.join(conditions)
            
            # Main KPI query
            query = f"""
                WITH filtered_reviews AS (
                    SELECT 
                        score,
                        "dateReview",
                        content
                    FROM reviews
                    WHERE {where_clause}
                    AND score IS NOT NULL
                ),
                sentiment_analysis AS (
                    SELECT 
                        COUNT(*) FILTER (WHERE score >= 7) as pos_count,
                        COUNT(*) FILTER (WHERE score <= 4) as neg_count,
                        COUNT(*) FILTER (WHERE score > 4 AND score < 7) as neu_count,
                        COUNT(*) as total_count
                    FROM filtered_reviews
                ),
                monthly_stats AS (
                    SELECT 
                        AVG(score) as avg_rating,
                        DATE_TRUNC('month', "dateReview") as month
                    FROM filtered_reviews
                    WHERE "dateReview" IS NOT NULL
                    GROUP BY DATE_TRUNC('month', "dateReview")
                    ORDER BY month DESC
                    LIMIT 2
                )
                SELECT 
                    (SELECT COUNT(*) FROM filtered_reviews) as review_count,
                    (SELECT AVG(score) FROM filtered_reviews) as avg_rating,
                    (SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY score) FROM filtered_reviews) as median_rating,
                    COALESCE((SELECT STDDEV(score) FROM filtered_reviews), 0) as rating_std,
                    COALESCE((SELECT pos_count::FLOAT / NULLIF(total_count, 0) FROM sentiment_analysis), 0) as pos_ratio,
                    COALESCE((SELECT neg_count::FLOAT / NULLIF(total_count, 0) FROM sentiment_analysis), 0) as neg_ratio,
                    COALESCE((SELECT neu_count::FLOAT / NULLIF(total_count, 0) FROM sentiment_analysis), 0) as neu_ratio,
                    (SELECT TO_CHAR(month, 'YYYY-MM') FROM monthly_stats LIMIT 1) as latest_month,
                    COALESCE(
                        (SELECT avg_rating FROM monthly_stats LIMIT 1) - 
                        (SELECT avg_rating FROM monthly_stats OFFSET 1 LIMIT 1),
                        0
                    ) as mom_change_avg_rating;
            """
            
            self.cur.execute(query, tuple(params))
            
            row = self.cur.fetchone()
            
            if not row or row[0] is None:
                return None
            
            return {
                "review_count": int(row[0]) if row[0] else 0,
                "avg_rating": float(row[1]) if row[1] else 0.0,
                "median_rating": float(row[2]) if row[2] else 0.0,
                "rating_std": float(row[3]) if row[3] else 0.0,
                "pos_ratio": float(row[4]) if row[4] else 0.0,
                "neg_ratio": float(row[5]) if row[5] else 0.0,
                "neu_ratio": float(row[6]) if row[6] else 0.0,
                "latest_month": row[7] if row[7] else None,
                "mom_change_avg_rating": float(row[8]) if row[8] else 0.0
            }
            
        except Exception as e:
            print(f"Error getting airline KPIs: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_rating_distribution_filtered(self, airline_name, start_date=None, end_date=None, destination=None):
        """Get rating distribution (1-5) with optional filters"""
        try:
            # Build WHERE clause
            conditions = ['LOWER("airlineName") = LOWER(%s)', 'score IS NOT NULL']
            params = [airline_name]
            
            if start_date:
                conditions.append('"dateReview" >= %s')
                params.append(start_date)
            
            if end_date:
                conditions.append('"dateReview" <= %s')
                params.append(end_date)
            
            if destination:
                conditions.append('(route LIKE %s OR route LIKE %s)')
                params.append(f'%{destination}%')
                params.append(f'%to {destination}%')
            
            where_clause = ' AND '.join(conditions)
            
            # Rating distribution query (1-5 scale, assuming score 0-10 maps to 1-5)
            self.cur.execute(
                f"""
                SELECT 
                    CASE 
                        WHEN score <= 2 THEN 1
                        WHEN score <= 4 THEN 2
                        WHEN score <= 6 THEN 3
                        WHEN score <= 8 THEN 4
                        WHEN score <= 10 THEN 5
                        ELSE NULL
                    END as rating_bucket,
                    COUNT(*) as count
                FROM reviews
                WHERE {where_clause}
                GROUP BY rating_bucket
                ORDER BY rating_bucket;
                """,
                tuple(params)
            )
            
            results = self.cur.fetchall()
            
            # Initialize all ratings with 0
            distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            
            for row in results:
                if row[0] and row[0] in distribution:
                    distribution[row[0]] = int(row[1])
            
            return [
                {"rating": rating, "count": distribution[rating]}
                for rating in sorted(distribution.keys())
            ]
            
        except Exception as e:
            print(f"Error getting rating distribution: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_rating_distribution_by_segment(self, airline_name, segment='seatType', start_date=None, end_date=None, destination=None, limit=10):
        """Get rating distribution (1-5) grouped by segment (seatType, typeOfTraveller, etc.)
        
        Args:
            airline_name: Airline name
            segment: Segment field name
            start_date: Start date filter
            end_date: End date filter
            destination: Destination filter
            limit: Maximum number of segments to return (default 10, top N by review count)
        """
        try:
            # Validate segment field
            valid_segments = ['seatType', 'typeOfTraveller', 'country', 'aircraft']
            if segment not in valid_segments:
                segment = 'seatType'
            
            # Build WHERE clause
            conditions = ['LOWER("airlineName") = LOWER(%s)', 'score IS NOT NULL', f'"{segment}" IS NOT NULL', f'"{segment}" != \'\'']
            params = [airline_name]
            
            if start_date:
                conditions.append('"dateReview" >= %s')
                params.append(start_date)
            
            if end_date:
                conditions.append('"dateReview" <= %s')
                params.append(end_date)
            
            if destination:
                conditions.append('(route LIKE %s OR route LIKE %s)')
                params.append(f'%{destination}%')
                params.append(f'%to {destination}%')
            
            where_clause = ' AND '.join(conditions)
            
            # Build query: where_clause appears twice, so we need params twice + limit
            # The LIMIT comes after both WHERE clauses, so parameter order is:
            # params for first WHERE, params for second WHERE, then limit
            query = f"""
                WITH segment_totals AS (
                    SELECT 
                        "{segment}" as segment_value,
                        COUNT(*) as total_count
                    FROM reviews
                    WHERE {where_clause}
                    GROUP BY "{segment}"
                    ORDER BY total_count DESC
                    LIMIT %s
                ),
                segment_ratings AS (
                    SELECT 
                        r."{segment}" as segment_value,
                        CASE 
                            WHEN r.score <= 2 THEN 1
                            WHEN r.score <= 4 THEN 2
                            WHEN r.score <= 6 THEN 3
                            WHEN r.score <= 8 THEN 4
                            WHEN r.score <= 10 THEN 5
                            ELSE NULL
                        END as rating_bucket,
                        COUNT(*) as count
                    FROM reviews r
                    INNER JOIN segment_totals st ON r."{segment}" = st.segment_value
                    WHERE {where_clause}
                    GROUP BY r."{segment}", rating_bucket
                )
                SELECT 
                    sr.segment_value,
                    sr.rating_bucket,
                    sr.count,
                    st.total_count
                FROM segment_ratings sr
                INNER JOIN segment_totals st ON sr.segment_value = st.segment_value
                ORDER BY st.total_count DESC, sr.segment_value, sr.rating_bucket;
            """
            
            # Parameter order: 
            # 1. params for first WHERE clause (segment_totals)
            # 2. limit for LIMIT clause
            # 3. params for second WHERE clause (segment_ratings)
            # Total: len(params) + 1 + len(params) = 2*len(params) + 1
            final_params = list(params) + [limit] + list(params)
            
            self.cur.execute(query, tuple(final_params))
            results = self.cur.fetchall()
            
            if not results:
                return []
            
            # Group by segment
            segment_data = {}
            segment_order = []  # Preserve order
            
            for row in results:
                segment_value = row[0] or 'Unknown'
                rating = row[1]
                count = int(row[2])
                total_count = int(row[3])
                
                if segment_value not in segment_data:
                    segment_data[segment_value] = {
                        'distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                        'total_count': total_count
                    }
                    segment_order.append(segment_value)
                
                if rating and rating in segment_data[segment_value]['distribution']:
                    segment_data[segment_value]['distribution'][rating] = count
            
            # Convert to array format, preserving order
            result = []
            for segment_value in segment_order:
                result.append({
                    "segment": segment_value,
                    "total_count": segment_data[segment_value]['total_count'],
                    "distribution": [
                        {"rating": rating, "count": segment_data[segment_value]['distribution'][rating]}
                        for rating in sorted(segment_data[segment_value]['distribution'].keys())
                    ]
                })
            
            return result
            
        except Exception as e:
            print(f"Error getting rating distribution by segment: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_monthly_trends(self, airline_name, start_date='2020-01-01', end_date=None, destination_top_n=5, use_materialized_view=False):
        """Get monthly trends for an airline
        
        Args:
            airline_name: Airline name
            start_date: Start date (default: '2020-01-01')
            end_date: End date (default: today)
            destination_top_n: Number of top destinations to include (default: 5)
            use_materialized_view: Whether to use materialized view (faster but may be stale)
        
        Returns:
            List of monthly data with review_count, avg_rating, sentiment_mean, destination_topN
        """
        try:
            from datetime import datetime, date
            import json
            
            if end_date is None:
                end_date = date.today().strftime('%Y-%m-%d')
            
            # Try to use materialized view if available and requested
            if use_materialized_view:
                try:
                    query = """
                        SELECT 
                            month,
                            review_count,
                            avg_rating,
                            sentiment_mean,
                            destination_top5 as destination_topN
                        FROM monthly_trends_mv
                        WHERE airline_name_lower = LOWER(%s)
                        AND month_date >= DATE_TRUNC('month', %s::date)
                        AND month_date <= DATE_TRUNC('month', %s::date)
                        ORDER BY month_date;
                    """
                    self.cur.execute(query, (airline_name, start_date, end_date))
                    results = self.cur.fetchall()
                    
                    if results:
                        return [
                            {
                                "month": row[0],
                                "review_count": int(row[1]) if row[1] else 0,
                                "avg_rating": float(row[2]) if row[2] else 0.0,
                                "sentiment_mean": float(row[3]) if row[3] else None,
                                "destination_topN": row[4] if row[4] else []
                            }
                            for row in results
                        ]
                except Exception as e:
                    # Fallback to regular query if materialized view doesn't exist
                    print(f"Materialized view not available, using regular query: {e}")
            
            # Regular query (always works, but slower for large datasets)
            conditions = ['LOWER("airlineName") = LOWER(%s)', '"dateReview" IS NOT NULL']
            params = [airline_name]
            
            if start_date:
                conditions.append('"dateReview" >= %s')
                params.append(start_date)
            
            if end_date:
                conditions.append('"dateReview" <= %s')
                params.append(end_date)
            
            where_clause = ' AND '.join(conditions)
            
            # Query for monthly trends
            query = f"""
                WITH monthly_stats AS (
                    SELECT 
                        DATE_TRUNC('month', "dateReview") as month,
                        COUNT(*) as review_count,
                        AVG(score) as avg_rating
                    FROM reviews
                    WHERE {where_clause}
                    AND score IS NOT NULL
                    GROUP BY DATE_TRUNC('month', "dateReview")
                ),
                monthly_destinations AS (
                    SELECT 
                        DATE_TRUNC('month', "dateReview") as month,
                        CASE 
                            WHEN route LIKE '%% to %%' THEN SPLIT_PART(route, ' to ', 2)
                            WHEN route LIKE '%% to%%' THEN TRIM(SPLIT_PART(route, ' to', 2))
                            ELSE NULL
                        END as destination,
                        COUNT(*) as route_count,
                        ROW_NUMBER() OVER (PARTITION BY DATE_TRUNC('month', "dateReview") ORDER BY COUNT(*) DESC) as rn
                    FROM reviews
                    WHERE {where_clause}
                    AND route IS NOT NULL
                    AND route != ''
                    AND route LIKE '%%to%%'
                    GROUP BY DATE_TRUNC('month', "dateReview"), destination
                    HAVING CASE 
                        WHEN route LIKE '%% to %%' THEN SPLIT_PART(route, ' to ', 2)
                        WHEN route LIKE '%% to%%' THEN TRIM(SPLIT_PART(route, ' to', 2))
                        ELSE NULL
                    END IS NOT NULL
                ),
                top_destinations AS (
                    SELECT 
                        month,
                        json_agg(
                            json_build_object('destination', destination, 'count', route_count) 
                            ORDER BY route_count DESC
                        ) as destinations
                    FROM monthly_destinations
                    WHERE rn <= %s
                    GROUP BY month
                )
                SELECT 
                    TO_CHAR(ms.month, 'YYYY-MM') as month,
                    ms.review_count,
                    ROUND(ms.avg_rating::NUMERIC, 2) as avg_rating,
                    NULL::NUMERIC as sentiment_mean,
                    COALESCE(td.destinations, '[]'::json) as destination_topN
                FROM monthly_stats ms
                LEFT JOIN top_destinations td ON ms.month = td.month
                ORDER BY ms.month;
            """
            
            params.append(destination_top_n)
            
            self.cur.execute(query, tuple(params))
            results = self.cur.fetchall()
            
            if not results:
                return []
            
            return [
                {
                    "month": row[0],
                    "review_count": int(row[1]) if row[1] else 0,
                    "avg_rating": float(row[2]) if row[2] else 0.0,
                    "sentiment_mean": float(row[3]) if row[3] else None,
                    "destination_topN": row[4] if row[4] else []
                }
                for row in results
            ]
            
        except Exception as e:
            print(f"Error getting monthly trends: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_monthly_trends(self, airline_name, start_date='2020-01-01', end_date=None, top_n_destinations=5):
        """Get monthly trends for an airline
        
        Returns:
            List of dicts with keys: month, review_count, avg_rating, sentiment_mean, destination_topN
        """
        try:
            from datetime import datetime, date
            
            if end_date is None:
                end_date = date.today().strftime('%Y-%m-%d')
            
            # Build WHERE clause with table alias 'r' for reviews table
            conditions = ['LOWER(r."airlineName") = LOWER(%s)', 'r.score IS NOT NULL', 'r."dateReview" IS NOT NULL']
            params = [airline_name]
            
            if start_date:
                conditions.append('r."dateReview" >= %s')
                params.append(start_date)
            
            if end_date:
                conditions.append('r."dateReview" <= %s')
                params.append(end_date)
            
            where_clause = ' AND '.join(conditions)
            
            # Main query: monthly aggregation with sentiment_mean from reviews_sentiment
            # Note: top_n_destinations is embedded directly in SQL (safe as it's an integer from function parameter)
            # We need to duplicate params for the CTEs that use the same WHERE clause
            query = f"""
                WITH monthly_stats AS (
                    SELECT 
                        DATE_TRUNC('month', r."dateReview") as month,
                        COUNT(*) as review_count,
                        AVG(r.score) as avg_rating
                    FROM reviews r
                    WHERE {where_clause}
                    GROUP BY DATE_TRUNC('month', r."dateReview")
                ),
                monthly_sentiment AS (
                    SELECT 
                        DATE_TRUNC('month', r."dateReview") as month,
                        AVG(rs.sentiment_score) as sentiment_mean
                    FROM reviews r
                    INNER JOIN reviews_sentiment rs 
                        ON r."reviewId" = rs.review_id 
                        AND r."airlineName" = rs."airlineName"
                    WHERE {where_clause}
                        AND rs.sentiment_score IS NOT NULL
                    GROUP BY DATE_TRUNC('month', r."dateReview")
                ),
                monthly_destinations AS (
                    SELECT 
                        DATE_TRUNC('month', r."dateReview") as month,
                        r.route,
                        COUNT(*) as route_count
                    FROM reviews r
                    WHERE {where_clause}
                        AND r.route IS NOT NULL
                        AND r.route != ''
                    GROUP BY DATE_TRUNC('month', r."dateReview"), r.route
                ),
                top_destinations_by_month AS (
                    SELECT 
                        month,
                        route,
                        route_count,
                        ROW_NUMBER() OVER (PARTITION BY month ORDER BY route_count DESC) as rn
                    FROM monthly_destinations
                )
                SELECT 
                    TO_CHAR(ms.month, 'YYYY-MM') as month,
                    ms.review_count,
                    ROUND(ms.avg_rating::numeric, 2) as avg_rating,
                    ROUND(COALESCE(mse.sentiment_mean, NULL)::numeric, 4) as sentiment_mean,
                    COALESCE(
                        json_agg(
                            json_build_object('destination', td.route, 'count', td.route_count)
                            ORDER BY td.route_count DESC
                        ) FILTER (WHERE td.rn <= {top_n_destinations}),
                        '[]'::json
                    ) as destination_topN
                FROM monthly_stats ms
                LEFT JOIN monthly_sentiment mse ON ms.month = mse.month
                LEFT JOIN top_destinations_by_month td ON ms.month = td.month AND td.rn <= {top_n_destinations}
                GROUP BY ms.month, ms.review_count, ms.avg_rating, mse.sentiment_mean
                ORDER BY ms.month;
            """
            
            # Duplicate params for the CTEs that use WHERE clause (monthly_stats, monthly_sentiment, monthly_destinations)
            execute_params = tuple(params + params + params)
            self.cur.execute(query, execute_params)
            results = self.cur.fetchall()
            
            if not results:
                return []
            
            trends = []
            for row in results:
                trends.append({
                    "month": row[0],
                    "review_count": int(row[1]) if row[1] else 0,
                    "avg_rating": float(row[2]) if row[2] else 0.0,
                    "sentiment_mean": float(row[3]) if row[3] is not None else None,  # Convert Decimal to float
                    "destination_topN": row[4] if row[4] else []
                })
            
            return trends
            
        except Exception as e:
            print(f"Error getting monthly trends: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_top_topics(self, airline_name: str, sentiment: str = 'pos', n: int = 10):
        """
        Get main topics for airline (optimized version)
        
        Args:
            airline_name: Airline name
            sentiment: 'pos' or 'neg'
            n: Number of topics to return
            
        Returns:
            List of topics, containing topic_id, top_words, human_label, review_count, avg_score
        """
        try:
            # Optimization: Get aggregated data first, avoid using LOWER() in JOIN
            # Use subquery for pre-aggregation, then JOIN for better performance
            self.cur.execute(
                """
                SELECT 
                    t.topic_id,
                    t.top_words,
                    t.human_label,
                    COALESCE(rt_stats.review_count, 0) as review_count,
                    COALESCE(rt_stats.avg_score, 0.0) as avg_score
                FROM topics t
                LEFT JOIN (
                    SELECT 
                        topic_id,
                        sentiment_bucket,
                        COUNT(review_id) as review_count,
                        AVG(topic_score) as avg_score
                    FROM reviews_topics
                    WHERE sentiment_bucket = %s
                        AND LOWER("airlineName") = LOWER(%s)
                    GROUP BY topic_id, sentiment_bucket
                ) rt_stats ON t.topic_id = rt_stats.topic_id 
                    AND t.sentiment_bucket = rt_stats.sentiment_bucket
                WHERE t.sentiment_bucket = %s
                    AND (t."airlineName" IS NULL OR LOWER(t."airlineName") = LOWER(%s))
                ORDER BY review_count DESC, avg_score DESC
                LIMIT %s;
                """,
                (sentiment, airline_name, sentiment, airline_name, n)
            )
            
            results = self.cur.fetchall()
            
            topics = []
            for row in results:
                topic_id, top_words, human_label, review_count, avg_score = row
                topics.append({
                    'topic_id': int(topic_id),
                    'top_words': top_words if isinstance(top_words, list) else list(top_words) if top_words else [],
                    'human_label': human_label or f'Topic {topic_id}',
                    'review_count': int(review_count),
                    'avg_score': float(avg_score) if avg_score else 0.0
                })
            
            return topics
            
        except Exception as e:
            print(f"Error getting top topics: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_wordcloud_from_sentiment(self, airline_name: str, limit: int = 500):
        """
        Generate wordcloud data from processed sentiment data (optimized version)
        
        Args:
            airline_name: Airline name
            limit: Number of reviews to use (default 500, take a portion from positive and negative reviews)
            
        Returns:
            Wordcloud data (pos_dict, neg_dict)
        """
        try:
            # Get processed sentiment data from reviews_sentiment table
            # Use JSONB aggregation (if available) or get from sentiment table
            # First try to get from sentiment table (if exists)
            
            # Method 1: Try to get from sentiment table (if data exists)
            try:
                self.cur.execute(
                    """
                    SELECT 
                        SUM(pos_dict) FILTER (WHERE sent_lab = 'Positive') as combined_pos_dict,
                        SUM(neg_dict) FILTER (WHERE sent_lab = 'Negative') as combined_neg_dict
                    FROM sentiment
                    WHERE text IN (
                        SELECT content FROM reviews 
                        WHERE LOWER("airlineName") = LOWER(%s)
                        LIMIT %s
                    );
                    """,
                    (airline_name, limit)
                )
                
                result = self.cur.fetchone()
                if result and (result[0] or result[1]):
                    # If data retrieved from sentiment table, return
                    import json
                    pos_dict = json.loads(result[0]) if result[0] else {}
                    neg_dict = json.loads(result[1]) if result[1] else {}
                    
                    pos_score = sum(abs(m.get('score', 0)) for m in pos_dict.values() if isinstance(m, dict))
                    neg_score = sum(abs(m.get('score', 0)) for m in neg_dict.values() if isinstance(m, dict))
                    
                    return {
                        "pos_dict": pos_dict,
                        "neg_dict": neg_dict,
                        "pos_score": pos_score,
                        "neg_score": neg_score,
                        "pos_count": len(pos_dict),
                        "neg_count": len(neg_dict),
                        "overall_score": pos_score - neg_score,
                        "overall_count": len(pos_dict) + len(neg_dict)
                    }
            except Exception:
                pass  # If sentiment table doesn't exist or query fails, use fallback method
            
            # Method 2: Get from reviews_sentiment table, use processed sentiment_score
            # For wordcloud, we need to extract keywords from review text
            # Use simplified method: get text from reviews_clean table, quickly extract keywords
            
            # Get reviews for this airline (take a portion from positive and negative)
            self.cur.execute(
                """
                SELECT rc.cleaned_text, rs.sentiment_label
                FROM reviews_clean rc
                JOIN reviews_sentiment rs 
                    ON rc.review_id = rs.review_id 
                    AND LOWER(rc."airlineName") = LOWER(rs."airlineName")
                WHERE LOWER(rc."airlineName") = LOWER(%s)
                    AND rc.cleaned_text IS NOT NULL
                    AND LENGTH(rc.cleaned_text) > 10
                ORDER BY RANDOM()
                LIMIT %s;
                """,
                (airline_name, limit)
            )
            
            reviews = self.cur.fetchall()
            
            if not reviews:
                return None
            
            # Use simplified keyword extraction (not using full sentiment model)
            # Extract common words from text as keywords
            import re
            from collections import Counter
            
            pos_words = []
            neg_words = []
            
            for text, sentiment_label in reviews:
                if not text:
                    continue
                
                # Simple tokenization (by spaces and punctuation)
                words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
                
                if sentiment_label == 'Positive':
                    pos_words.extend(words)
                elif sentiment_label == 'Negative':
                    neg_words.extend(words)
            
            # Count word frequency
            pos_counter = Counter(pos_words)
            neg_counter = Counter(neg_words)
            
            # Convert to wordcloud format
            pos_dict = {word: {'score': count * 0.1} for word, count in pos_counter.most_common(100)}
            neg_dict = {word: {'score': count * 0.1} for word, count in neg_counter.most_common(100)}
            
            pos_score = sum(m['score'] for m in pos_dict.values())
            neg_score = sum(m['score'] for m in neg_dict.values())
            
            return {
                "pos_dict": pos_dict,
                "neg_dict": neg_dict,
                "pos_score": pos_score,
                "neg_score": neg_score,
                "pos_count": len(pos_dict),
                "neg_count": len(neg_dict),
                "overall_score": pos_score - neg_score,
                "overall_count": len(pos_dict) + len(neg_dict)
            }
            
        except Exception as e:
            print(f"Error getting wordcloud from sentiment: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def close(self):
        if self.conn:
            self.cur.close()
            self.conn.close()