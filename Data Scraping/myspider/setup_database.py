#!/usr/bin/env python3
"""
Database setup script (Python version)
Alternative to psql command-line tool, configure database directly via Python
"""

import psycopg
import sys
import os
from pathlib import Path

def read_sql_file(file_path):
    """Read SQL file content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Error: File not found {file_path}")
        return None
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None

def setup_database():
    """Setup database"""
    print("=" * 60)
    print("Airline Review Database Setup Script (Python Version)")
    print("=" * 60)
    print()
    
    # Get current system username as default (macOS Homebrew PostgreSQL uses system username by default)
    import getpass
    default_user = getpass.getuser()
    
    # Get user input
    print("Please enter PostgreSQL connection information:")
    print("(Press Enter to use default values)")
    print()
    print(f"💡 Tip: macOS Homebrew PostgreSQL default user is '{default_user}' (your system username)")
    print(f"   Usually no password needed, just press Enter")
    print()
    
    db_user = input(f"Username (default: {default_user}): ").strip() or default_user
    db_password = input("Password (default: empty, press Enter): ").strip()
    db_host = input("Host (default: localhost): ").strip() or "localhost"
    db_port = input("Port (default: 5432): ").strip() or "5432"
    db_name = input("Database name (default: airline_db): ").strip() or "airline_db"
    
    print()
    print("=" * 60)
    print("Configuration:")
    print(f"  User: {db_user}")
    print(f"  Host: {db_host}")
    print(f"  Port: {db_port}")
    print(f"  Database: {db_name}")
    print("=" * 60)
    print()
    
    confirm = input("Confirm to create database and tables? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled")
        return False
    
    # Build connection string
    # If no password, use connection string without password (macOS defaults to peer authentication)
    if db_password:
        dsn_postgres = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/postgres"
        dsn_db = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    else:
        # macOS Homebrew defaults to peer authentication, no password needed
        dsn_postgres = f"postgresql://{db_user}@{db_host}:{db_port}/postgres"
        dsn_db = f"postgresql://{db_user}@{db_host}:{db_port}/{db_name}"
    
    try:
        print()
        print("Step 1/4: Connecting to PostgreSQL...")
        conn = psycopg.connect(dsn_postgres, autocommit=True)
        print("✅ Connection successful")
        
        print()
        print("Step 2/4: Creating database...")
        try:
            conn.execute(f'CREATE DATABASE "{db_name}";')
            print(f"✅ Database '{db_name}' created successfully")
        except psycopg.errors.DuplicateDatabase:
            print(f"⚠️  Database '{db_name}' already exists, skipping creation")
        finally:
            conn.close()
        
        print()
        print("Step 3/4: Connecting to new database and creating tables...")
        conn = psycopg.connect(dsn_db)
        cur = conn.cursor()
        
        # Read and execute SQL file
        script_dir = Path(__file__).parent
        sql_file = script_dir / "init_database.sql"
        
        if not sql_file.exists():
            print(f"❌ Error: File not found {sql_file}")
            return False
        
        # Use inline SQL statements directly to avoid complexity of parsing SQL files
        # This avoids handling dollar quotes, DO blocks, and other complex syntax
        print("Creating table structure...")
        
        key_statements = [
            # Create airlines table
            """CREATE TABLE IF NOT EXISTS airlines (
                name TEXT PRIMARY KEY,
                image TEXT,
                "reviewCount" INTEGER,
                score NUMERIC(3, 1),
                "calculatedReviewCount" INTEGER DEFAULT 0,
                "seatComfort" NUMERIC(3, 1),
                "cabinStaffService" NUMERIC(3, 1),
                "foodBeverages" NUMERIC(3, 1),
                "inflightEntertainment" NUMERIC(3, 1),
                "groundService" NUMERIC(3, 1),
                "wifiConnectivity" NUMERIC(3, 1),
                "valueForMoney" NUMERIC(3, 1),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );""",
            
            # Create reviews table
            """CREATE TABLE IF NOT EXISTS reviews (
                "reviewId" TEXT NOT NULL,
                "userName" TEXT NOT NULL,
                "airlineName" TEXT NOT NULL,
                title TEXT,
                score INTEGER,
                content TEXT,
                "verifiedType" TEXT,
                country TEXT,
                "dateReview" DATE,
                aircraft TEXT,
                "typeOfTraveller" TEXT,
                "seatType" TEXT,
                route TEXT,
                "dateFlown" TEXT,
                "seatComfort" INTEGER,
                "cabinStaffService" INTEGER,
                "foodBeverages" INTEGER,
                "inflightEntertainment" INTEGER,
                "groundService" INTEGER,
                "wifiConnectivity" INTEGER,
                "valueForMoney" INTEGER,
                recommended TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY ("reviewId", "airlineName")
            );""",
            
            # Create sentiment table
            """CREATE TABLE IF NOT EXISTS sentiment (
                id SERIAL PRIMARY KEY,
                text TEXT NOT NULL,
                submit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_lab TEXT,
                pos_dict JSONB,
                neg_dict JSONB
            );""",
            
            # Create indexes
            """CREATE INDEX IF NOT EXISTS idx_reviews_airline_name ON reviews("airlineName");""",
            """CREATE INDEX IF NOT EXISTS idx_reviews_date_review ON reviews("dateReview");""",
            """CREATE INDEX IF NOT EXISTS idx_reviews_score ON reviews(score);""",
            """CREATE INDEX IF NOT EXISTS idx_sentiment_submit_time ON sentiment(submit_time);"""
        ]
        
        # Execute each SQL statement
        for i, statement in enumerate(key_statements, 1):
            try:
                cur.execute(statement)
            except psycopg.errors.DuplicateTable:
                conn.rollback()
                # Table already exists, continue
            except psycopg.errors.DuplicateObject:
                conn.rollback()
                # Object already exists, continue
            except Exception as e:
                conn.rollback()
                error_msg = str(e).lower()
                if "already exists" not in error_msg and "duplicate" not in error_msg:
                    print(f"  ⚠️  Warning (statement {i}): {str(e)[:100]}")
        
        # Commit all successful statements
        conn.commit()
        print("✅ Table structure created successfully")
        
        # Verify tables were created successfully
        try:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cur.fetchall()
        except Exception as e:
            conn.rollback()
            print(f"⚠️  Error verifying tables: {e}")
            tables = []
        
        print()
        print("Created tables:")
        for table in tables:
            print(f"  ✅ {table[0]}")
        
        cur.close()
        conn.close()
        
        print()
        print("Step 4/4: Creating .env file...")
        env_file = script_dir / ".env"
        
        if env_file.exists():
            overwrite = input(".env file already exists, overwrite? (y/n): ").strip().lower()
            if overwrite != 'y':
                print("Keeping existing .env file")
                return True
        
        # Create .env file
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(f"# PostgreSQL database connection configuration\n")
            f.write(f"POSTGRES_DSN={dsn_db}\n")
        
        print(f"✅ .env file created: {env_file}")
        
        print()
        print("=" * 60)
        print("✅ Database setup completed!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Run test script to verify connection:")
        print("   python test_connection.py")
        print()
        print("2. Start scraping data:")
        print("   scrapy crawl reviews")
        print()
        
        return True
        
    except psycopg.OperationalError as e:
        print(f"❌ Connection error: {e}")
        print()
        print("Please check:")
        print("1. Is PostgreSQL service running?")
        print("   macOS: brew services start postgresql@18")
        print("2. Are username and password correct?")
        print("3. Are host and port correct?")
        return False
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = setup_database()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nCancelled")
        sys.exit(1)

