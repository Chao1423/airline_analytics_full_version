#!/usr/bin/env python3
"""
Refresh monthly trends materialized view
Recommended to run daily via cron job
"""

import psycopg
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
POSTGRES_DSN = os.getenv("POSTGRES_DSN")

def refresh_monthly_trends():
    """Refresh monthly trends materialized view"""
    conn = psycopg.connect(POSTGRES_DSN)
    cur = conn.cursor()
    
    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔄 Starting refresh of monthly_trends_mv...")
        
        # Refresh materialized view
        cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY monthly_trends_mv;")
        conn.commit()
        
        # Get statistics
        cur.execute("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT "airlineName") as total_airlines,
                MIN(month) as earliest_month,
                MAX(month) as latest_month
            FROM monthly_trends_mv;
        """)
        
        stats = cur.fetchone()
        
        print(f"✅ Refresh completed successfully!")
        print(f"   Total rows: {stats[0]}")
        print(f"   Total airlines: {stats[1]}")
        print(f"   Date range: {stats[2]} to {stats[3]}")
        
    except Exception as e:
        print(f"❌ Error refreshing materialized view: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    refresh_monthly_trends()
