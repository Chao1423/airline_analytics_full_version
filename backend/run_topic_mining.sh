#!/bin/bash

# Topic mining execution script

cd "$(dirname "$0")"
source ../venv/bin/activate

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔍 Starting Topic Mining Pipeline${NC}"
echo ""

# Check dependencies
echo -e "${YELLOW}📦 Checking dependencies...${NC}"
python -c "import bertopic; import sentence_transformers; import umap; import hdbscan" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Missing dependencies. Installing...${NC}"
    pip install bertopic sentence-transformers umap-learn hdbscan
fi

# Check database tables
echo -e "${YELLOW}🗄️  Checking database tables...${NC}"
python -c "
from postgres_db import PostgresClient
from dotenv import load_dotenv
import os
load_dotenv()
db = PostgresClient(os.getenv('POSTGRES_DSN'))
cur = db.cur
cur.execute(\"SELECT COUNT(*) FROM reviews_clean WHERE lang = 'en'\")
clean_count = cur.fetchone()[0]
cur.execute(\"SELECT COUNT(*) FROM reviews_sentiment\")
sentiment_count = cur.fetchone()[0]
print(f'English reviews in reviews_clean: {clean_count}')
print(f'Reviews with sentiment: {sentiment_count}')
db.close()
"

# Get parameters
AIRLINE="${1:-}"
SENTIMENT="${2:-both}"
MIN_SIZE="${3:-10}"
N_TOPICS="${4:-}"

if [ -z "$AIRLINE" ]; then
    echo -e "${YELLOW}⚠️  No airline specified. Mining topics for all airlines.${NC}"
    echo -e "${YELLOW}   Usage: $0 [airline_name] [sentiment] [min_topic_size] [n_topics]${NC}"
    echo ""
    AIRLINE_CMD=""
else
    echo -e "${GREEN}✈️  Mining topics for: ${AIRLINE}${NC}"
    AIRLINE_CMD="\"$AIRLINE\""
fi

echo -e "${GREEN}📊 Parameters:${NC}"
echo "   Sentiment: $SENTIMENT"
echo "   Min Topic Size: $MIN_SIZE"
[ -n "$N_TOPICS" ] && echo "   Number of Topics: $N_TOPICS"
echo ""

# Run topic mining
echo -e "${GREEN}🚀 Running topic mining...${NC}"
echo ""

if [ -n "$N_TOPICS" ]; then
    python topic_mining.py $AIRLINE_CMD "$SENTIMENT" "$MIN_SIZE" "$N_TOPICS"
else
    python topic_mining.py $AIRLINE_CMD "$SENTIMENT" "$MIN_SIZE"
fi

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Topic mining completed successfully!${NC}"
    echo ""
    echo -e "${YELLOW}📊 Checking results...${NC}"
    python -c "
from postgres_db import PostgresClient
from dotenv import load_dotenv
import os
load_dotenv()
db = PostgresClient(os.getenv('POSTGRES_DSN'))
cur = db.cur
cur.execute(\"SELECT COUNT(*) FROM topics\")
topic_count = cur.fetchone()[0]
cur.execute(\"SELECT COUNT(*) FROM reviews_topics\")
review_topic_count = cur.fetchone()[0]
print(f'Topics created: {topic_count}')
print(f'Review-topic associations: {review_topic_count}')
db.close()
"
else
    echo -e "${RED}❌ Topic mining failed with exit code $EXIT_CODE${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Done!${NC}"

