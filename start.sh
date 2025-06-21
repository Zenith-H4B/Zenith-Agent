#!/bin/bash

# Zenith Agent Startup Script
echo "🚀 Starting Zenith Agent..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create necessary directories
mkdir -p logs
mkdir -p static
mkdir -p mongo-init

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
ENVIRONMENT=development
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=zenith_agent
GOOGLE_API_KEY=your_google_api_key_here
RESEND_API_KEY=your_resend_api_key_here
EOF
    echo "✅ Created .env file. Please update it with your API keys."
fi

# Build and start the services
echo "🔨 Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services are running!"
    echo ""
    echo "🌐 Zenith Agent Dashboard: http://localhost:8000"
    echo "📊 API Documentation: http://localhost:8000/docs"
    echo "🔍 Health Check: http://localhost:8000/health"
    echo "📋 Logs Stream: http://localhost:8000/logs/stream"
    echo "🗄️  MongoDB: mongodb://localhost:27017"
    echo ""
    echo "📝 To expose to external networks, use ngrok:"
    echo "   ngrok http 8000"
    echo ""
    echo "🛑 To stop services: docker-compose down"
    echo "📊 To view logs: docker-compose logs -f"
else
    echo "❌ Some services failed to start. Check the logs:"
    docker-compose logs
fi