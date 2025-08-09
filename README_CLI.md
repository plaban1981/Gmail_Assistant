# Gmail CLI Assistant

A command-line interface for Gmail email management using Arcade AI and LangGraph.

## 🎯 Overview

This CLI script provides the same functionality as the Streamlit app but through a command-line interface. Users can search emails, create drafts, manage drafts, and more using natural language commands.

## 🚀 Features

- **Email Search**: Search and list emails using natural language
- **Draft Management**: Create, list, update, and delete draft emails
- **Email Operations**: Send emails, reply to emails, and more
- **Natural Language**: Use natural language commands for all operations
- **Professional Templates**: Automatic professional email bodies
- **Error Handling**: Comprehensive error handling and user guidance

## 📋 Prerequisites

1. **Python 3.8+** installed
2. **Gmail account** with API access
3. **Arcade AI API key** (for Gmail tools)
4. **OpenAI API key** (for AI processing)

## 🛠️ Installation

1. **Clone or download the script:**
   ```bash
   # If you have the script files
   ls gmail_cli_assistant.py
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements_cli.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the same directory with:
   ```env
   ARCADE_API_KEY=your_arcade_api_key_here
   OPENAIAPIKEY=your_openai_api_key_here
   EMAIL=your_email@gmail.com
   MODEL_CHOICE=gpt-4o-mini
   ```

## 🎯 Usage

### Basic Usage

1. **Run the script:**
   ```bash
   python gmail_cli_assistant.py
   ```

2. **Use natural language commands:**
   ```
   📧 Gmail Assistant > Show me emails from today
   📧 Gmail Assistant > Create a new email to test@example.com with subject 'Test' and body 'Hello'
   📧 Gmail Assistant > Show me my drafts
   ```

### Available Commands

#### 1. Email Search
- `"Show me emails from today"`
- `"Find emails from john@example.com"`
- `"Search for emails about meetings"`
- `"List top 5 emails from this week"`

#### 2. Draft Management
- `"Create a new email to test@example.com with subject 'Test' and body 'Hello'"`
- `"Draft a reply to the latest email"`
- `"Show me my drafts"`
- `"Delete draft with subject 'Test'"`

#### 3. Email Operations
- `"Send the draft with subject 'Test'"`
- `"Update draft with subject 'Test' with new body 'Updated content'"`
- `"Get email with ID 12345"`

#### 4. General Commands
- `help` - Show help message
- `quit` or `exit` - Exit the application
- `clear` - Clear the screen

## 🔧 Examples

### Example 1: Search Emails
```
📧 Gmail Assistant > Show me emails from today
🔄 Processing...
==================================================
🤖 Response:
==================================================
I found 5 emails from today:

1. Subject: Meeting Reminder
   From: john@example.com
   Date: Today 10:30 AM
   Snippet: Hi, just a reminder about our meeting...

2. Subject: Project Update
   From: sarah@company.com
   Date: Today 9:15 AM
   Snippet: Here's the latest update on the project...
==================================================
```

### Example 2: Create Draft Email
```
📧 Gmail Assistant > Create a new email to test@example.com with subject 'Meeting Request' and body 'Hi, I would like to schedule a meeting.'
🔄 Processing...
==================================================
🤖 Response:
==================================================
✅ Draft Email Created Successfully!

I've created a draft email for you with the following details:

Subject: Meeting Request
Recipient: test@example.com
Body: Hi, I would like to schedule a meeting.

📍 Where to find your draft:
- Gmail Web Interface: https://mail.google.com/mail/u/0/#drafts
- Gmail Mobile App: Open Gmail app → Tap the menu (☰) → Select "Drafts"
- Gmail Desktop: Look for "Drafts" in the left sidebar

The draft has been saved to your Gmail drafts folder. You can review, edit, and send it when you're ready!
==================================================
```

### Example 3: List Drafts
```
📧 Gmail Assistant > Show me my drafts
🔄 Processing...
==================================================
🤖 Response:
==================================================
✅ Draft Emails Retrieved!

I've retrieved your draft emails. Here are your saved drafts:

1. Subject: Meeting Request
   From: your_email@gmail.com
   Date: Today 2:30 PM
   Snippet: Hi, I would like to schedule a meeting...

2. Subject: Project Update
   From: your_email@gmail.com
   Date: Yesterday 4:15 PM
   Snippet: Here's the latest update on the project...

📍 Access your drafts:
- Gmail Web Interface: https://mail.google.com/mail/u/0/#drafts
- Gmail Mobile App: Open Gmail app → Tap the menu (☰) → Select "Drafts"
- Gmail Desktop: Look for "Drafts" in the left sidebar
==================================================
```

## 🔍 Troubleshooting

### Common Issues

1. **Missing API Keys**
   ```
   ❌ Error: ARCADE_API_KEY not found in environment variables
   ```
   **Solution**: Make sure your `.env` file contains the required API keys.

2. **Authorization Issues**
   ```
   🔐 Authorization required for Gmail_ListEmails...
   ```
   **Solution**: Follow the authorization prompts when they appear.

3. **Empty Draft Bodies**
   ```
   ⚠️ Draft Email Creation Issue
   ```
   **Solution**: Always provide body content when creating drafts, or the AI will create a professional template.

### Error Messages

- **"Authorization required"**: Follow the authorization prompts
- **"No response received"**: Check your internet connection and API keys
- **"Error processing command"**: Try rephrasing your request or check the help

## 🎯 Tips

1. **Use Natural Language**: "Show me emails from LinkedIn" instead of technical commands
2. **Be Specific**: "Create a draft email to john@example.com about the meeting"
3. **Check Drafts**: Use "Show me my drafts" to see all saved drafts
4. **Professional Templates**: The AI will create professional email bodies when none are provided

## 🔧 Advanced Usage

### Custom Commands

You can create custom commands by combining multiple operations:

```
📧 Gmail Assistant > Find emails from john@example.com and draft a reply to the latest one
```

### Batch Operations

```
📧 Gmail Assistant > Show me all drafts and delete the one with subject 'Test'
```

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify your API keys are correct
3. Ensure you have the required dependencies installed
4. Try rephrasing your request

## 🎉 Success!

Once you have the CLI assistant running, you can:

- ✅ Search emails using natural language
- ✅ Create professional draft emails
- ✅ Manage your Gmail drafts
- ✅ Send emails and replies
- ✅ Handle all Gmail operations through AI

**Happy emailing! 🚀** 