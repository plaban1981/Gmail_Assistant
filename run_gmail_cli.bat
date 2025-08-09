@echo off
echo 🚀 Starting Gmail CLI Assistant...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if the script exists
if not exist "gmail_cli_assistant.py" (
    echo ❌ Error: gmail_cli_assistant.py not found
    echo Please make sure the script is in the current directory
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️ Warning: .env file not found
    echo Please create a .env file with your API keys:
    echo ARCADE_API_KEY=your_arcade_api_key_here
    echo OPENAIAPIKEY=your_openai_api_key_here
    echo EMAIL=your_email@gmail.com
    echo MODEL_CHOICE=gpt-4o-mini
    echo.
    pause
)

REM Run the CLI assistant
echo 🔧 Starting Gmail CLI Assistant...
python gmail_cli_assistant.py

REM Pause if there was an error
if errorlevel 1 (
    echo.
    echo ❌ An error occurred while running the Gmail CLI Assistant
    pause
) 