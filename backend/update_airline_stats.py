#!/usr/bin/env python3
"""
Update airline aggregated statistics
Calculate and update airlines table's score and calculatedReviewCount from reviews table
"""

import psycopg
from dotenv import load_dotenv
import os

load_dotenv()
POSTGRES_DSN = os.getenv("POSTGRES_DSN")

def update_airline_stats():
    """Update statistics for all airlines"""
    conn = psycopg.connect(POSTGRES_DSN)
    cur = conn.cursor()
    
    try:
        print("🔄 Starting to update airline statistics...")
        print()
        
        # Get all airlines
        cur.execute("SELECT name FROM airlines;")
        airlines = cur.fetchall()
        
        total = len(airlines)
        updated = 0
        
        for i, (airline_name,) in enumerate(airlines, 1):
            try:
                # Calculate statistics for this airline
                cur.execute("""
                    SELECT 
                        COUNT(*) as review_count,
                        AVG(score) as avg_score,
                        AVG("seatComfort") as avg_seat_comfort,
                        AVG("cabinStaffService") as avg_cabin_staff,
                        AVG("foodBeverages") as avg_food,
                        AVG("inflightEntertainment") as avg_entertainment,
                        AVG("groundService") as avg_ground,
                        AVG("wifiConnectivity") as avg_wifi,
                        AVG("valueForMoney") as avg_value
                    FROM reviews
                    WHERE "airlineName" = %s;
                """, (airline_name,))
                
                result = cur.fetchone()
                
                if result and result[0] > 0:  # If there are reviews
                    review_count = result[0]
                    avg_score = result[1]
                    avg_seat = result[2]
                    avg_cabin = result[3]
                    avg_food = result[4]
                    avg_entertainment = result[5]
                    avg_ground = result[6]
                    avg_wifi = result[7]
                    avg_value = result[8]
                    
                    # Update airlines table
                    cur.execute("""
                        UPDATE airlines
                        SET 
                            "calculatedReviewCount" = %s,
                            score = %s,
                            "seatComfort" = %s,
                            "cabinStaffService" = %s,
                            "foodBeverages" = %s,
                            "inflightEntertainment" = %s,
                            "groundService" = %s,
                            "wifiConnectivity" = %s,
                            "valueForMoney" = %s
                        WHERE name = %s;
                    """, (
                        review_count,
                        avg_score,
                        avg_seat,
                        avg_cabin,
                        avg_food,
                        avg_entertainment,
                        avg_ground,
                        avg_wifi,
                        avg_value,
                        airline_name
                    ))
                    
                    updated += 1
                    
                    if i % 50 == 0:
                        print(f"  Processed {i}/{total} airlines...")
                
            except Exception as e:
                print(f"  ⚠️  Error processing {airline_name}: {e}")
                continue
        
        conn.commit()
        
        print()
        print("=" * 60)
        print(f"✅ Update completed!")
        print(f"   Total: {total} airlines")
        print(f"   Updated: {updated} airlines with data")
        print("=" * 60)
        
        # Verify results
        cur.execute("""
            SELECT COUNT(*) 
            FROM airlines 
            WHERE score IS NOT NULL AND "calculatedReviewCount" > 0;
        """)
        count = cur.fetchone()[0]
        print(f"\n📊 Now {count} airlines have complete statistics")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    update_airline_stats()

