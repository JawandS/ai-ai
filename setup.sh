#!/bin/bash

# Experimental Economics Platform Setup Script

echo "🧪 Setting up Experimental Economics Platform..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env .env.example
    echo "Please edit .env file with your OpenAI API key"
else
    echo "✅ .env file already exists"
fi

# Initialize database
echo "🗄️  Initializing database..."
python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database tables created successfully!')
"

echo "🚀 Setup complete! Run 'python app.py' to start the server"
echo "📱 Visit http://localhost:5000 to access the platform"