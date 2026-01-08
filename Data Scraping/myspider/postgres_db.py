from dotenv import load_dotenv, find_dotenv
import os
import psycopg

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
                    "reviewId", "userName", "airlineName",
                    title, score, content, "verifiedType", 
                    country, "dateReview",
                    aircraft, "typeOfTraveller", "seatType", route, "dateFlown",
                    "seatComfort", "cabinStaffService", "foodBeverages",
                    "inflightEntertainment", "groundService", "wifiConnectivity",
                    "valueForMoney", recommended
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

    def close(self):
        if self.conn:
            self.cur.close()
            self.conn.close()

            