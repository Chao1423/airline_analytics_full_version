# Airline Dashboard - AirSight

A comprehensive airline review analytics dashboard with sentiment analysis, topic mining, and RAG-powered insights.

![Video Preview](./video_preview.png)

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Data Collection](#data-collection)
- [Running the Application](#running-the-application)
- [Pipelines](#pipelines)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)

## Features

- **Dashboard Analytics**: KPI metrics, rating distributions, monthly trends, and airline comparisons
- **Sentiment Analysis**: Automated sentiment analysis pipeline for review classification
- **Topic Mining**: BERTopic-based topic extraction for positive and negative reviews
- **Aspect-Based Analysis**: Multi-dimensional scoring (seat comfort, food, service, etc.)
- **RAG Chatbot**: AI-powered Q&A system using DeepSeek API for insights
- **Review Search**: Advanced filtering by time, rating, sentiment, topic, aspect, and destination
- **Analytics Tools**: OLS regression for topic drivers and rating change simulation

## Prerequisites

- **Python 3.12+**
- **Node.js 18+** and npm
- **PostgreSQL 14+**
- **Git**

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Chao1423/airline_analytics_full_version
cd airline_analytics_full_version
```

### 2. Set Up Python Virtual Environment

```bash
# Create virtual environment
sudo apt install -y python3.12-venv
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Set Up Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

## Configuration

### Environment Variables

Create `.env` files in the following locations:

#### 1. Backend `.env` (`backend/.env`)

```env
POSTGRES_DSN=postgresql://username:password@localhost:5432/airline_db
DEEPSEEK_API_KEY=your_deepseek_api_key_here  # Optional, for RAG feature
```

#### 2. Frontend `.env` (`frontend/.env`)

```env
VITE_API_URL=http://localhost:8000
```

#### 3. Scraper `.env` (`Data Scraping/myspider/.env`)

```env
POSTGRES_DSN=postgresql://username:password@localhost:5432/airline_db
```

**Note**: Replace `username`, `password`, and `airline_db` with your actual PostgreSQL credentials.

## Database Setup

### 1. Install PostgreSQL

**macOS (Homebrew)**:
```bash
brew install postgresql@18
brew services start postgresql@18
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows**: Download from [PostgreSQL official website](https://www.postgresql.org/download/windows/)

### 2. Create Database and Tables

#### Option A: Using Python Script (Recommended)

```bash
cd "Data Scraping/myspider"
source ../../venv/bin/activate
python setup_database.py
```

The script will:
- Prompt for database credentials
- Create the database if it doesn't exist
- Create all required tables
- Generate `.env` file

#### Option B: Manual Setup

```bash
# Create database
createdb airline_db

# Run SQL scripts
psql -U username -d airline_db -f "Data Scraping/myspider/init_database.sql"
psql -U username -d airline_db -f backend/create_sentiment_tables.sql
psql -U username -d airline_db -f backend/create_topic_tables_v2.sql
psql -U username -d airline_db -f backend/create_topic_driver_tables.sql
psql -U username -d airline_db -f backend/create_rag_tables.sql
psql -U username -d airline_db -f backend/create_monthly_trends_materialized_view.sql
psql -U username -d airline_db -f backend/add_optimization_indexes.sql
```

### 3. Verify Database Connection

```bash
cd "Data Scraping/myspider"
source ../../venv/bin/activate
python -c "from postgres_db import PostgresClient; from dotenv import load_dotenv; import os; load_dotenv(); db = PostgresClient(os.getenv('POSTGRES_DSN')); print('✅ Connection successful'); db.close()"
```

## Data Collection

### Option 1: Web Scraping (Recommended)

```bash
cd "Data Scraping/myspider"
source ../../venv/bin/activate
scrapy crawl reviews
```

The scraper will:
- Crawl airline reviews from the target website
- Store data in PostgreSQL
- Handle retries and error logging

**Note**: Make sure to respect the website's robots.txt and rate limits.

### Option 2: Import SQL Dump

If you have a SQL dump file:

```bash
psql -U username -d airline_db < your_data_dump.sql
```

### Option 3: Manual Data Entry

Use the database client or API endpoints to insert data manually.

## Running the Application

### Quick Start (Recommended)

```bash
# Start both backend and frontend
./start_all.sh

# Stop all services
./stop_all.sh
```

### Manual Start

#### Terminal 1 - Backend

```bash
./start_backend.sh
```

Backend will be available at: http://127.0.0.1:8000
API Documentation: http://127.0.0.1:8000/docs

#### Terminal 2 - Frontend

```bash
./start_frontend.sh
```

Frontend will be available at: http://localhost:3000
(For Chome user，please use incognito browsing otherwise the browser will block the access)

## Pipelines

### 1. Sentiment Analysis Pipeline

Processes reviews to extract sentiment scores and cleaned text.

#### Setup

```bash
cd backend
source ../venv/bin/activate

# Install additional dependencies
pip install langdetect>=1.0.9

# Create tables (if not already created)
psql -U username -d airline_db -f create_sentiment_tables.sql
```

#### Run Pipeline

```bash
# Process all new reviews
python sentiment_pipeline.py --batch-size 100

# Process limited number of reviews (testing)
python sentiment_pipeline.py --batch-size 50 --max-reviews 100

# Generate report only
python sentiment_pipeline.py --report-only
```

⚠️The initial runtime is up to 40hrs, however it won't affect other ongoing jobs. New data processed will be displayed automaticly.

#### Schedule with Cron

```bash
./setup_sentiment_cron.sh
```

This sets up a daily cron job at 3:00 AM to process new reviews.

### 2. Topic Mining Pipeline

Extracts topics from positive and negative reviews using BERTopic.

#### Setup

```bash
cd backend
source ../venv/bin/activate

# Install dependencies
pip install bertopic sentence-transformers umap-learn hdbscan

# Create tables
python create_topic_tables_v2.py
```

#### Run Topic Mining

```bash
# Mine topics for all airlines (both positive and negative)
python topic_mining.py

# Mine topics for specific airline
python topic_mining.py "EVA Air" both

# Mine only positive topics
python topic_mining.py "EVA Air" pos

# Mine only negative topics
python topic_mining.py "EVA Air" neg
```

**Parameters**:
- `airline_name`: Airline name (optional, default: all airlines)
- `sentiment`: 'pos', 'neg', or 'both' (default: 'both')
- `min_topic_size`: Minimum topic size (default: 10)
- `n_topics`: Number of topics (optional, auto-determined if not specified)

#### Using Shell Script

```bash
./run_topic_mining.sh
```

### 3. RAG Embeddings Generation

Generate embeddings for the RAG chatbot feature.

#### Setup

```bash
cd backend
source ../venv/bin/activate

# Create RAG tables
python create_rag_tables.py
```

#### Generate Embeddings

```bash
# Generate for all airlines
python generate_embeddings.py

# Generate for specific airline
python generate_embeddings.py "Delta Air Lines"

# With custom batch size
python generate_embeddings.py "Delta Air Lines" 200
```

**Estimated Time**:
- 1,000 reviews: ~2-3 minutes
- 10,000 reviews: ~20-30 minutes

**Note**: If `pgvector` extension is not available, the system will automatically use text-based search.

### 4. Monthly Trends Materialized View

Refresh the monthly trends materialized view for faster queries.

```bash
cd backend
source ../venv/bin/activate

# Refresh manually
python refresh_monthly_trends.py

# Or use shell script
./refresh_monthly_trends.sh
```

#### Schedule with Cron

```bash
./setup_cron_job.sh
```

## Project Structure

```
airline-dashboard/
├── backend/                 # FastAPI backend
│   ├── main.py             # Main API application
│   ├── postgres_db.py      # Database client
│   ├── sentiment_pipeline.py  # Sentiment analysis pipeline
│   ├── topic_mining.py     # Topic mining pipeline
│   ├── rag_service.py      # RAG chatbot service
│   ├── generate_embeddings.py  # Embeddings generator
│   └── *.sql               # Database schema scripts
├── frontend/               # React frontend
│   ├── src/
│   │   ├── pages/         # Page components
│   │   ├── components/    # Reusable components
│   │   └── hooks/        # Custom React hooks
│   └── package.json
├── Data Scraping/         # Scrapy web scraper
│   └── myspider/
│       └── spiders/       # Spider definitions
├── start_backend.sh       # Backend startup script
├── start_frontend.sh      # Frontend startup script
├── start_all.sh          # Start both services
├── stop_all.sh           # Stop all services
└── requirements.txt      # Python dependencies
```

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

### Key Endpoints

- `GET /api/airlines/{airline}/kpi` - Get airline KPI metrics
- `GET /api/airlines/{airline}/monthly-trends` - Get monthly trends
- `GET /api/airlines/{airline}/top-topics` - Get top topics
- `GET /api/airlines/{airline}/drivers` - Get topic drivers (OLS regression)
- `POST /api/simulate` - Simulate rating changes
- `POST /api/rag/ask` - Ask AirSight chatbot
- `GET /api/reviews/search` - Search reviews with filters

## Troubleshooting

### Backend Issues

**Port 8000 already in use**:
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9
```

**Database connection error**:
- Verify `POSTGRES_DSN` in `backend/.env`
- Check PostgreSQL is running: `brew services list | grep postgresql`
- Test connection: `psql $POSTGRES_DSN`

**Module not found**:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Issues

**Port 3000 already in use**:
```bash
# Find and kill the process
lsof -ti:3000 | xargs kill -9
```

**API connection error**:
- Verify `VITE_API_URL` in `frontend/.env`
- Check backend is running on port 8000

### Pipeline Issues

**Sentiment pipeline errors**:
- Ensure `langdetect` is installed: `pip install langdetect>=1.0.9`
- Check tables exist: `psql -d airline_db -c "\dt"`

**Topic mining errors**:
- Ensure BERTopic dependencies are installed
- Check sentiment data exists: Run sentiment pipeline first
- Verify minimum review count (recommended: 100+ reviews)

**RAG chatbot returns no results**:
- Generate embeddings: `python generate_embeddings.py`
- Check `review_embeddings` table: `SELECT COUNT(*) FROM review_embeddings;`
- Verify DeepSeek API key is set

### Database Issues

**Table does not exist**:
```bash
# Run appropriate SQL script
psql -U username -d airline_db -f backend/create_<table_name>_tables.sql
```

**Permission denied**:
- Ensure PostgreSQL user has proper permissions
- Check `.env` file has correct credentials

## License

See `backend/license.txt` for license information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions, please open an issue on GitHub.

## Demostration video: how to use:

https://youtu.be/NY5uz8wZI4E

