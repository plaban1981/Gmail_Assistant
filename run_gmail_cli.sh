#!/bin/bash

echo "🚀 Starting Gmail CLI Assistant..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Check if the script exists
if [ ! -f "gmail_cli_assistant.py" ]; then
    echo "❌ Error: gmail_cli_assistant.py not found"
    echo "Please make sure the script is in the current directory"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Please create a .env file with your API keys:"
    echo "ARCADE_API_KEY=your_arcade_api_key_here"
    echo "OPENAIAPIKEY=your_openai_api_key_here"
    echo "EMAIL=your_email@gmail.com"
    echo "MODEL_CHOICE=gpt-4o-mini"
    echo
    read -p "Press Enter to continue anyway..."
fi

# Check if virtual environment exists and activate it if it does
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
fi

# Run the CLI assistant
echo "🔧 Starting Gmail CLI Assistant..."
python3 gmail_cli_assistant.py

# Check if there was an error
if [ $? -ne 0 ]; then
    echo
    echo "❌ An error occurred while running the Gmail CLI Assistant"
    read -p "Press Enter to exit..."
fi 