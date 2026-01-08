#!/usr/bin/env python3
"""
Create topic_driver_results table
"""

import psycopg
import os
from dotenv import load_dotenv

def create_tables():
    load_dotenv()
    dsn = os.getenv('POSTGRES_DSN')
    
    if not dsn:
        print("❌ Error: POSTGRES_DSN not found in environment variables")
        return
    
    try:
        conn = psycopg.connect(dsn)
        cur = conn.cursor()
        
        # Read SQL file
        sql_file = os.path.join(os.path.dirname(__file__), 'create_topic_driver_tables.sql')
        with open(sql_file, 'r') as f:
            sql = f.read()
        
        # Execute SQL
        cur.execute(sql)
        conn.commit()
        
        print("✅ Successfully created topic_driver_results table")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_tables()

