#!/bin/bash

# Database quick setup script
# Usage: ./setup_database.sh

set -e  # Exit immediately on error

echo "=========================================="
echo "Airline Review Database Setup Script"
echo "=========================================="
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ Error: psql command not found"
    echo "Please install PostgreSQL first"
    echo ""
    echo "macOS: brew install postgresql@15"
    echo "Linux: sudo apt install postgresql"
    exit 1
fi

echo "✅ PostgreSQL is installed"
echo ""

# Prompt user for database information
read -p "Enter PostgreSQL username (default: postgres): " DB_USER
DB_USER=${DB_USER:-postgres}

read -sp "Enter password: " DB_PASSWORD
echo ""

read -p "Enter database host (default: localhost): " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "Enter database port (default: 5432): " DB_PORT
DB_PORT=${DB_PORT:-5432}

read -p "Enter database name (default: airline_db): " DB_NAME
DB_NAME=${DB_NAME:-airline_db}

echo ""
echo "=========================================="
echo "Configuration:"
echo "  User: $DB_USER"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "=========================================="
echo ""

read -p "Confirm to create database and tables? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Cancelled"
    exit 0
fi

# Set environment variable
export PGPASSWORD="$DB_PASSWORD"

echo ""
echo "Step 1/3: Creating database..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || {
    echo "⚠️  Database may already exist, continuing..."
}

echo "Step 2/3: Executing table creation script..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f init_database.sql

echo "Step 3/3: Creating .env file..."
ENV_FILE=".env"
if [ -f "$ENV_FILE" ]; then
    read -p ".env file already exists, overwrite? (y/n): " OVERWRITE
    if [ "$OVERWRITE" != "y" ] && [ "$OVERWRITE" != "Y" ]; then
        echo "Keeping existing .env file"
        exit 0
    fi
fi

# Create .env file
cat > "$ENV_FILE" << EOF
# PostgreSQL database connection configuration
POSTGRES_DSN=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME
EOF

echo "✅ .env file created"
echo ""

# Clean up environment variable
unset PGPASSWORD

echo "=========================================="
echo "✅ Database setup completed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Run test script to verify connection:"
echo "   python test_connection.py"
echo ""
echo "2. Start scraping data:"
echo "   scrapy crawl reviews"
echo ""

