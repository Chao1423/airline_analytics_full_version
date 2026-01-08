#!/usr/bin/env python3
"""
Quickly view database structure and data statistics
"""

import psycopg
from dotenv import load_dotenv, find_dotenv
import os
from tabulate import tabulate

def view_database():
    """View database structure and data"""
    print("=" * 80)
    print("Database Structure and Data Statistics")
    print("=" * 80)
    print()
    
    # Load environment variables
    load_dotenv(find_dotenv())
    dsn = os.getenv("POSTGRES_DSN")
    
    if not dsn:
        print("❌ Error: POSTGRES_DSN environment variable not found")
        print("Please ensure .env file exists and contains POSTGRES_DSN")
        return False
    
    try:
        # Connect to database
        conn = psycopg.connect(dsn)
        cur = conn.cursor()
        
        print("✅ Database connection successful")
        print()
        
        # 1. View all tables
        print("=" * 80)
        print("📊 Database Table List")
        print("=" * 80)
        cur.execute("""
            SELECT table_name, 
                   pg_size_pretty(pg_total_relation_size('"' || table_name || '"')) as size
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cur.fetchall()
        
        table_data = []
        for table in tables:
            table_name = table[0]
            table_size = table[1]
            
            # Get record count
            try:
                cur.execute(f'SELECT COUNT(*) FROM "{table_name}";')
                count = cur.fetchone()[0]
                table_data.append([table_name, count, table_size])
            except:
                table_data.append([table_name, "N/A", table_size])
        
        print(tabulate(table_data, headers=["Table Name", "Record Count", "Size"], tablefmt="grid"))
        print()
        
        # 2. View airlines table data
        print("=" * 80)
        print("✈️  Airline Data (airlines)")
        print("=" * 80)
        cur.execute("""
            SELECT name, "reviewCount", score, "calculatedReviewCount"
            FROM airlines
            ORDER BY "reviewCount" DESC NULLS LAST
            LIMIT 20;
        """)
        airlines = cur.fetchall()
        
        if airlines:
            airline_data = [[row[0], row[1] or 0, f"{row[2]:.1f}" if row[2] else "N/A", row[3] or 0] 
                           for row in airlines]
            print(tabulate(airline_data, 
                          headers=["Airline", "Review Count", "Score", "Calculated Review Count"], 
                          tablefmt="grid"))
            print()
            
            # Statistics
            cur.execute("SELECT COUNT(*) FROM airlines;")
            total_airlines = cur.fetchone()[0]
            print(f"📈 Total: {total_airlines} airlines")
        else:
            print("⚠️  No data available")
        print()
        
        # 3. View reviews table statistics
        print("=" * 80)
        print("📝 Review Data Statistics (reviews)")
        print("=" * 80)
        cur.execute("""
            SELECT 
                COUNT(*) as total_reviews,
                COUNT(DISTINCT "airlineName") as total_airlines,
                AVG(score) as avg_score,
                MIN("dateReview") as earliest_review,
                MAX("dateReview") as latest_review
            FROM reviews;
        """)
        stats = cur.fetchone()
        
        if stats and stats[0]:
            stats_data = [
                ["Total Reviews", f"{stats[0]:,}"],
                ["Number of Airlines", stats[1]],
                ["Average Score", f"{stats[2]:.2f}" if stats[2] else "N/A"],
                ["Earliest Review", stats[3].strftime("%Y-%m-%d") if stats[3] else "N/A"],
                ["Latest Review", stats[4].strftime("%Y-%m-%d") if stats[4] else "N/A"]
            ]
            print(tabulate(stats_data, headers=["Statistic", "Value"], tablefmt="grid"))
            print()
            
            # Statistics by airline
            print("📊 Top 10 Airlines by Review Count:")
            cur.execute("""
                SELECT "airlineName", COUNT(*) as review_count
                FROM reviews
                GROUP BY "airlineName"
                ORDER BY review_count DESC
                LIMIT 10;
            """)
            top_airlines = cur.fetchall()
            if top_airlines:
                top_data = [[row[0], f"{row[1]:,}"] for row in top_airlines]
                print(tabulate(top_data, headers=["Airline", "Review Count"], tablefmt="grid"))
        else:
            print("⚠️  No data available")
        print()
        
        # 4. View sentiment table data
        print("=" * 80)
        print("💭 Sentiment Analysis Data (sentiment)")
        print("=" * 80)
        cur.execute("SELECT COUNT(*) FROM sentiment;")
        sentiment_count = cur.fetchone()[0]
        print(f"📈 Total: {sentiment_count} sentiment analysis records")
        print()
        
        # 5. View table structure
        print("=" * 80)
        print("🔍 Table Structure Details")
        print("=" * 80)
        
        for table_name in ['airlines', 'reviews', 'sentiment']:
            print(f"\n📋 {table_name} table structure:")
            cur.execute("""
                SELECT column_name, data_type, character_maximum_length, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            columns = cur.fetchall()
            
            if columns:
                col_data = []
                for col in columns:
                    col_name = col[0]
                    col_type = col[1]
                    col_length = f"({col[2]})" if col[2] else ""
                    nullable = "NULL" if col[3] == "YES" else "NOT NULL"
                    col_data.append([col_name, f"{col_type}{col_length}", nullable])
                
                print(tabulate(col_data, headers=["Field Name", "Data Type", "Nullable"], tablefmt="grid"))
        
        # 6. View recent review examples
        print()
        print("=" * 80)
        print("📄 Recent Review Examples (Latest 5)")
        print("=" * 80)
        cur.execute("""
            SELECT "airlineName", title, score, "dateReview", LEFT(content, 100) as content_preview
            FROM reviews
            WHERE "dateReview" IS NOT NULL
            ORDER BY "dateReview" DESC
            LIMIT 5;
        """)
        recent_reviews = cur.fetchall()
        
        if recent_reviews:
            for i, review in enumerate(recent_reviews, 1):
                print(f"\n{i}. {review[0]} - {review[1]}")
                print(f"   Score: {review[2]}/10 | Date: {review[3]}")
                print(f"   Content preview: {review[4]}...")
        else:
            print("⚠️  No data available")
        
        cur.close()
        conn.close()
        
        print()
        print("=" * 80)
        print("✅ View completed")
        print("=" * 80)
        
        return True
        
    except psycopg.OperationalError as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        view_database()
    except KeyboardInterrupt:
        print("\n\nCancelled")
    except ImportError as e:
        if "tabulate" in str(e):
            print("❌ Missing dependency: tabulate")
            print("Please run: pip install tabulate")
        else:
            raise

