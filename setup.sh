#!/bin/bash

# Setup script for AI Agent System

echo "🚀 Setting up AI Agent Task Allocation System..."

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your actual API keys and configuration"
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Check if MongoDB is running
echo "🔍 Checking MongoDB connection..."
python -c "
import pymongo
try:
    client = pymongo.MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=2000)
    client.server_info()
    print('✅ MongoDB connection successful')
except:
    print('❌ MongoDB connection failed. Please ensure MongoDB is running.')
"

echo "✅ Setup complete!"
echo ""
echo "🔧 Next steps:"
echo "1. Edit the .env file with your API keys"
echo "2. Ensure MongoDB is running"
echo "3. Run the application with: python main.py"
echo ""
echo "📚 API Documentation will be available at: http://localhost:8000/docs"
