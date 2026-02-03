#!/bin/bash
# Celery worker startup script for Marketing2 project

set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check required environment variables
if [ -z "$DASHSCOPE_API_KEY" ]; then
    echo "ERROR: DASHSCOPE_API_KEY not set"
    exit 1
fi

# Default values
REDIS_URL=${REDIS_URL:-redis://localhost:6379/0}
DATABASE_URL=${DATABASE_URL:-postgresql://admin:password@localhost:5432/marketing2}

echo "=== Marketing2 Celery Worker ==="
echo "Redis: $REDIS_URL"
echo "Database: $DATABASE_URL"
echo ""

# Parse arguments
WORKER_TYPE=${1:-ai}  # ai, video, or all
CONCURRENCY=${2:-4}

case $WORKER_TYPE in
    ai)
        echo "Starting AI Generation Worker (queue: ai_generation, concurrency: $CONCURRENCY)"
        exec celery -A app.celery_app worker \
            --loglevel=info \
            --queues=ai_generation \
            --concurrency=$CONCURRENCY \
            --max-tasks-per-child=100 \
            --hostname=ai-worker@%h
        ;;
    
    video)
        echo "Starting Video Processing Worker (queue: video_processing, concurrency: 1)"
        exec celery -A app.celery_app worker \
            --loglevel=info \
            --queues=video_processing \
            --concurrency=1 \
            --max-tasks-per-child=50 \
            --hostname=video-worker@%h
        ;;
    
    all)
        echo "Starting All-Purpose Worker (all queues, concurrency: $CONCURRENCY)"
        exec celery -A app.celery_app worker \
            --loglevel=info \
            --queues=default,ai_generation,video_processing \
            --concurrency=$CONCURRENCY \
            --max-tasks-per-child=100 \
            --hostname=all-worker@%h
        ;;
    
    *)
        echo "Usage: $0 [ai|video|all] [concurrency]"
        echo ""
        echo "Examples:"
        echo "  $0 ai 4       # Start AI worker with 4 concurrent tasks"
        echo "  $0 video      # Start video worker (always concurrency=1)"
        echo "  $0 all 8      # Start worker handling all queues"
        exit 1
        ;;
esac
