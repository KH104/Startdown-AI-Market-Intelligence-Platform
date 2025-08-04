#!/bin/bash

# StartDown API Deployment Script
set -e

echo "🚀 Starting StartDown API deployment..."

# Configuration
APP_NAME="startdown-api"
DOCKER_IMAGE="startdown/api:latest"
ENVIRONMENT=${1:-"staging"}

echo "📋 Deployment Configuration:"
echo "   App Name: $APP_NAME"
echo "   Environment: $ENVIRONMENT"
echo "   Docker Image: $DOCKER_IMAGE"

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t $DOCKER_IMAGE .

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down || true

# Start new deployment
echo "🌟 Starting new deployment..."
if [ "$ENVIRONMENT" = "production" ]; then
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
else
    docker-compose up -d
fi

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Run database migrations
echo "📊 Running database migrations..."
docker-compose exec api alembic upgrade head

# Load sample data (only for staging)
if [ "$ENVIRONMENT" = "staging" ]; then
    echo "📋 Loading sample data..."
    docker-compose exec api python scripts/sample_data_loader.py
fi

# Health check
echo "🏥 Performing health check..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Health check passed!"
        break
    fi
    echo "   Attempt $i/30 - waiting for service..."
    sleep 2
done

# Final verification
echo "🔍 Final verification..."
API_STATUS=$(curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null || echo "unknown")

if [ "$API_STATUS" = "healthy" ]; then
    echo "🎉 Deployment successful!"
    echo ""
    echo "📍 Service URLs:"
    echo "   API: http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
    echo "   Health Check: http://localhost:8000/health"
    echo ""
    echo "🔑 Test Credentials:"
    echo "   Admin: admin@startdown.com / admin123"
    echo "   Sales: sales@startdown.com / sales123"
    echo "   Demo: demo@startdown.com / demo123"
else
    echo "❌ Deployment failed - health check unsuccessful"
    echo "📋 Container logs:"
    docker-compose logs api
    exit 1
fi