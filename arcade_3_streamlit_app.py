"""
Streamlit UI for Arcade AI Agent with LangGraph and Supabase Authentication.
"""

import os
import streamlit as st
from dotenv import load_dotenv
import supabase
from supabase.client import Client
import uuid
import asyncio
import sys
import re
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore

# Import our agent
from arcade_3_agent_with_memory import build_graph

# Load environment variables
load_dotenv()

print("🚀 Starting Arcade AI Agent Streamlit App...")
print(f"📁 Working directory: {os.getcwd()}")

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL", "")
supabase_key = os.environ.get("SUPABASE_KEY", "")
supabase_client = supabase.create_client(supabase_url, supabase_key)

print(f"🔗 Supabase URL configured: {'Yes' if supabase_url else 'No'}")
print(f"🔑 Supabase key configured: {'Yes' if supabase_key else 'No'}")

# Get other environment variables
arcade_api_key = os.environ.get("ARCADE_API_KEY")
openai_api_key = os.environ.get("OPENAIAPIKEY")
print(f"🤖 OpenAI API key configured: {openai_api_key}")
model_choice = os.environ.get("MODEL_CHOICE")
database_url = os.environ.get("DATABASE_URL")

print(f"🎮 Arcade API key configured: {'Yes' if arcade_api_key else 'No'}")
print(f"🤖 OpenAI API key configured: {'Yes' if openai_api_key else 'No'}")
print(f"🧠 Model choice: {model_choice}")
print(f"🗄️ Database URL configured: {'Yes' if database_url else 'No'}")

# Check if we have the minimum required configuration
if not arcade_api_key or not openai_api_key:
    print("❌ ERROR: Missing required API keys (ARCADE_API_KEY or OPENAI_API_KEY)")
    st.error("❌ Missing required API keys. Please check your .env file.")
    st.stop()

# Streamlit configuration for light mode
st.set_page_config(
    page_title="Arcade AI Agent",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Comprehensive Light Mode CSS
st.markdown("""
<style>
/* Force light mode throughout the app */
[data-testid="stAppViewContainer"] {
    background-color: #ffffff !important;
}

[data-testid="stSidebar"] {
    background-color: #f0f2f6 !important;
}

[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    background-color: #f0f2f6 !important;
}

.main .block-container {
    background-color: #ffffff !important;
}

.stApp {
    background-color: #ffffff !important;
}

/* Ensure all text is dark in light mode */
p, h1, h2, h3, h4, h5, h6, span, div {
    color: #262730 !important;
}

/* Chat interface light mode */
.stChatMessage {
    background-color: #ffffff !important;
    border: 1px solid #e0e0e0 !important;
}

.stChatMessage [data-testid="chatMessage"] {
    color: #262730 !important;
}

/* Input fields light mode */
.stTextInput > div > div > input {
    background-color: #ffffff !important;
    color: #262730 !important;
}

/* Button styling for light mode */
.stButton > button {
    background-color: #ffffff !important;
    color: #262730 !important;
    border: 1px solid #e0e0e0 !important;
}

/* Email content styling for light mode */
.email-content {
    background-color: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 16px;
    margin: 8px 0;
    color: #212529 !important;
}

.email-header {
    border-bottom: 1px solid #dee2e6;
    padding-bottom: 8px;
    margin-bottom: 12px;
    color: #212529 !important;
}

.email-subject {
    font-weight: bold;
    color: #495057 !important;
    font-size: 1.1em;
}

.email-meta {
    color: #6c757d !important;
    font-size: 0.9em;
    margin: 4px 0;
}

.email-body {
    background-color: white;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    padding: 12px;
    margin-top: 8px;
    color: #212529 !important;
}

.email-snippet {
    font-style: italic;
    color: #495057 !important;
    background-color: #f8f9fa;
    padding: 8px;
    border-radius: 4px;
    margin: 8px 0;
}

/* Ensure all text in email content is visible */
.email-content * {
    color: #212529 !important;
}

.email-content p {
    color: #212529 !important;
}

.email-content div {
    color: #212529 !important;
}

/* Override any white text in email content */
.email-content, .email-content * {
    color: #212529 !important;
}

/* Force all text in email content to be visible */
.email-content div[style*="color: white"], 
.email-content div[style*="color: #fff"], 
.email-content div[style*="color: #ffffff"] {
    color: #212529 !important;
}

/* Ensure markdown content in email is visible */
.email-content .markdown-text-container {
    color: #212529 !important;
}

.email-content .markdown-text-container * {
    color: #212529 !important;
}

/* Light mode specific overrides */
.stMarkdown {
    color: #212529 !important;
}

.stMarkdown * {
    color: #212529 !important;
}

/* Ensure chat messages are visible in light mode */
.stChatMessage {
    background-color: #ffffff !important;
}

.stChatMessage * {
    color: #212529 !important;
}
</style>
""", unsafe_allow_html=True)

# Custom CSS for better formatting
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .sidebar .sidebar-content {
        background-color: #f0f2f6;
    }
    .chat-container {
        max-width: 900px;
        margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True)

# Authentication functions
def sign_up(email, password, full_name):
    print(f"📝 Attempting to sign up user: {email} with name: {full_name}")
    try:
        response = supabase_client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name
                }
            }
        })
        if response and response.user:
            print(f"✅ Sign up successful for user: {email}")
            st.session_state.authenticated = True
            st.session_state.user = response.user
            st.rerun()
        else:
            print(f"❌ Sign up failed for user: {email} - No user in response")
        return response
    except Exception as e:
        print(f"❌ Error during sign up for {email}: {str(e)}")
        st.error(f"Error signing up: {str(e)}")
        return None

def sign_in(email, password):
    print(f"🔐 Attempting to sign in user: {email}")
    try:
        response = supabase_client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if response and response.user:
            print(f"✅ Sign in successful for user: {email}")
            # Store user info directly in session state
            st.session_state.authenticated = True
            st.session_state.user = response.user
            st.rerun()
        else:
            print(f"❌ Sign in failed for user: {email} - No user in response")
        return response
    except Exception as e:
        print(f"❌ Error during sign in for {email}: {str(e)}")
        st.error(f"Error signing in: {str(e)}")
        return None

def sign_out():
    print("🚪 Attempting to sign out user")
    try:
        supabase_client.auth.sign_out()
        print("✅ Sign out successful")
        # Clear authentication-related session state
        st.session_state.authenticated = False
        st.session_state.user = None
        # Clear conversation history
        st.session_state.messages = []
        # Generate new thread ID for next session
        st.session_state.thread_id = str(uuid.uuid4())
        print(f"🆔 Generated new thread ID: {st.session_state.thread_id[:8]}...")
        # Set a flag to trigger rerun on next render
        st.session_state.logout_requested = True
    except Exception as e:
        print(f"❌ Error during sign out: {str(e)}")
        st.error(f"Error signing out: {str(e)}")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    print("💬 Initialized empty messages list in session state")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    print("🔒 Set authenticated to False in session state")

if "user" not in st.session_state:
    st.session_state.user = None
    print("👤 Set user to None in session state")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
    print(f"🆔 Generated new thread ID: {st.session_state.thread_id[:8]}...")

# Check for logout flag and clear it after processing
if st.session_state.get("logout_requested", False):
    print("🔄 Processing logout request - clearing session state")
    st.session_state.logout_requested = False
    st.rerun()

# Function to clean conversation history
def clear_processed_emails():
    """Clear the global processed emails set."""
    global _processed_emails_global, _processed_email_content_hashes, _processed_email_subjects
    _processed_emails_global.clear()
    _processed_email_content_hashes.clear()
    _processed_email_subjects.clear()
    print(f"🧹 Cleared all processed email tracking sets")

def clean_conversation_history():
    """Clear the conversation history and reset the session state."""
    if 'messages' in st.session_state:
        st.session_state.messages = []
    
    # Clear the global processed emails set
    clear_processed_emails()
    
    print("🧹 Conversation history cleared")
    st.success("Conversation history cleared!")
    st.rerun()

def display_authorization_message(auth_url, tool_name):
    """Display authorization message prominently in the chat interface."""
    print(f"🔐 Creating authorization message for {tool_name}")
    
    # Create a prominent authorization message
    auth_message = f"""
🔐 **Authorization Required**

The agent needs access to your **{tool_name}** to complete your request.

**Please click the link below to authorize:**

🔗 **[Click here to authorize Gmail access]({auth_url})**

⏳ *Waiting for authorization...*
    """
    
    # Add to chat history
    st.session_state.messages.append({
        "role": "assistant", 
        "content": auth_message
    })
    
    print(f"📝 Added authorization message to chat history")
    return auth_message

def format_email_response(content):
    """Format email response content to match Arcade playground style."""
    if not content:
        return content
    
    # Clean up the content
    content = content.strip()
    
    # Remove any null values
    content = content.replace('null', '').replace('None', '').strip()
    
    # If it's an email response, format it nicely
    if 'emails from' in content.lower() or 'subject:' in content.lower():
        # Split into lines and clean up
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and line.lower() != 'null':
                cleaned_lines.append(line)
        
        # Rejoin with proper spacing
        formatted_content = '\n\n'.join(cleaned_lines)
        return formatted_content
    
    return content

# Custom writer function for streaming
class StreamlitWriter:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.content = ""
        self.processed_emails = set()  # Track processed emails to avoid duplicates
        self.email_content_processed = False  # Track if email content has been processed
        self.processed_content_hashes = set()  # Track all processed content hashes
        self.finalized = False  # Track if content has been finalized
        print(f"📝 Initialized StreamlitWriter for streaming content")
    
    def reset(self):
        """Reset the writer state for a new conversation."""
        self.content = ""
        self.processed_emails.clear()
        self.email_content_processed = False
        self.processed_content_hashes.clear()
        self.finalized = False
        print(f"🔄 StreamlitWriter reset for new conversation")
    
    def __call__(self, text):
        print(f"📤 Writing chunk: {text[:50]}{'...' if len(text) > 50 else ''}")
        
        # Skip null or empty content
        if not text or text.strip() == '' or text.lower() == 'null':
            print(f"⚠️ Skipping null or empty text: {text}")
            return
        
        # Check for duplicate content using hash
        content_hash = hash(text.strip())
        if content_hash in self.processed_content_hashes:
            print(f"⚠️ Skipping duplicate content (hash: {content_hash})")
            return
        
        self.processed_content_hashes.add(content_hash)
        
        # Check if content is already formatted (contains HTML)
        if '<div' in text or '<span' in text:
            # Content is already formatted, add it directly
            if not self._is_duplicate_content(text):
                self.content += text
                print(f"📧 Added already formatted content")
            else:
                print(f"⚠️ Skipping duplicate formatted content")
        elif self._is_email_content(text):
            # Only process email content once per session
            if not self.email_content_processed:
                formatted_text = self._format_email_content(text)
                # Check for duplicates before adding
                if not self._is_duplicate_content(formatted_text):
                    self.content += formatted_text
                    self.email_content_processed = True
                    print(f"📧 Processed email content for this session")
                else:
                    print(f"⚠️ Skipping duplicate email content")
            else:
                print(f"⚠️ Skipping email content - already processed for this session")
        else:
            # Add the content directly for non-email content
            if not self._is_duplicate_content(text):
                self.content += text
                print(f"📧 Added non-email content")
            else:
                print(f"⚠️ Skipping duplicate non-email content")
        
        print(f"📊 Total content length: {len(self.content)} characters")
        print(f"📋 Current content preview: {self.content[-200:] if len(self.content) > 200 else self.content}")
    
    def finalize(self):
        """Finalize the content and update the placeholder once."""
        if not self.content.strip() or self.finalized:
            print(f"⚠️ Skipping finalize - content already finalized or empty")
            return
        
        self.finalized = True
        print(f"🔧 Finalizing content display: {len(self.content)} characters")
        
        # Check if content contains HTML
        if '<div' in self.content or '<span' in self.content:
            # Ensure all text is visible by adding color styles
            styled_content = self._ensure_visible_text(self.content)
            self.placeholder.markdown(styled_content, unsafe_allow_html=True)
        else:
            formatted_content = self.content.replace("\n", "  \n")  # Add line breaks for markdown
            self.placeholder.markdown(formatted_content)
        
        print(f"✅ Finalized content display: {len(self.content)} characters")
    
    def _is_duplicate_content(self, content):
        """Check if content is a duplicate of previously processed content."""
        # Create a simple hash of the content for comparison
        content_hash = hash(content.strip())
        if content_hash in self.processed_emails:
            return True
        self.processed_emails.add(content_hash)
        return False
    
    def _ensure_visible_text(self, content):
        """Ensure all text in the content is visible with proper colors."""
        # Add color styles to ensure visibility
        if 'style="color:' not in content:
            # If no color styles are present, add them
            content = content.replace('<div', '<div style="color: #212529;"')
        return content
    
    def _is_email_content(self, text):
        """Check if the text contains email-like content."""
        # First, check if content is already formatted (contains HTML)
        if '<div' in text or '<span' in text:
            return False
        
        email_indicators = [
            'emails from', 'subject:', 'from:', 'date:', 'to:', 
            'snippet:', 'full email:', 'thread_id', 'body'
        ]
        return any(indicator in text.lower() for indicator in email_indicators)
    
    def _format_email_content(self, text):
        """Format email content to match Arcade playground style."""
        try:
            # Try to parse as JSON first
            import json
            if text.strip().startswith('{') and text.strip().endswith('}'):
                data = json.loads(text)
                # Use the global formatting function for consistency
                return _format_json_email_data(data)
            
            # If not JSON, try to format as plain text email
            return _format_plain_text_email(text)
        except (json.JSONDecodeError, Exception) as e:
            print(f"⚠️ Could not parse as JSON, formatting as plain text: {e}")
            return _format_plain_text_email(text)

def stream_agent_response(user_input: str, graph, config: dict, placeholder):
    """Stream the agent response to the placeholder."""
    print(f"🤖 Starting agent response for input: {user_input[:50]}{'...' if len(user_input) > 50 else ''}")
    print(f"⚙️ Config: {config}")
    
    # Build conversation history from existing messages
    messages = []
    if 'messages' in st.session_state:
        print(f"📚 Building conversation history from {len(st.session_state.messages)} existing messages")
        for i, msg in enumerate(st.session_state.messages, 1):
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
                print(f"  📝 Added user message {i}: {msg['content'][:30]}{'...' if len(msg['content']) > 30 else ''}")
            elif msg["role"] == "assistant":
                # Skip assistant messages that contain errors
                if "Error processing request" not in msg["content"]:
                    messages.append(AIMessage(content=msg["content"]))
                    print(f"  🤖 Added assistant message {i}: {msg['content'][:30]}{'...' if len(msg['content']) > 30 else ''}")
    
    # Add current user message
    messages.append(HumanMessage(content=user_input))
    print(f"📝 Added current user message: {user_input[:50]}{'...' if len(user_input) > 50 else ''}")
    
    inputs = {"messages": messages}
    print(f"📦 Prepared inputs with {len(messages)} total messages")
    
    # Initialize writer for streaming
    writer = StreamlitWriter(placeholder)
    print(f"📝 Initialized StreamlitWriter for streaming content")
    
    # Reset writer if this is a new conversation (no previous messages)
    if len(messages) <= 1:
        writer.reset()
    
    # Track processed content to avoid duplicates
    processed_content = set()
    full_response = ""
    email_content_processed = False  # Track if we've already processed email content
    tool_calls_made = []  # Track tool calls for summary
    
    print("🔄 Starting to stream agent response...")
    try:
        for chunk in graph.stream(inputs, config=config, stream_mode="values"):
            if isinstance(chunk, dict) and "messages" in chunk:
                last_message = chunk["messages"][-1]
                
                # Check for content in the message
                if hasattr(last_message, 'content') and last_message.content:
                    content = str(last_message.content)
                    if content and content.strip() and content.lower() != 'null':
                        # Check if this content has already been processed
                        content_hash = hash(content.strip())
                        if content_hash not in processed_content:
                            processed_content.add(content_hash)
                            
                            # Check if this is email content
                            if _is_email_like_content(content):
                                # Only process email content once per response
                                if not email_content_processed:
                                    print(f"🔧 Processing email content: {content[:100]}...")
                                    formatted_content = _format_email_response(content)
                                    if formatted_content:  # Only add if not empty (not a duplicate)
                                        print(f"🔧 Adding formatted email content: {formatted_content[:100]}...")
                                        writer(formatted_content)
                                        full_response += formatted_content
                                        email_content_processed = True
                                        print(f"📧 Processed email content for this response")
                                    else:
                                        print(f"⚠️ Skipped duplicate email content")
                                else:
                                    print(f"⚠️ Skipping duplicate email content in same response")
                            else:
                                # For non-email content, check if it's just repeating the user's query
                                if content.strip().lower() == user_input.strip().lower():
                                    print(f"⚠️ Skipping user query repetition: {content[:50]}...")
                                else:
                                    print(f"🔧 Adding non-email content: {content[:100]}...")
                                    writer(content)
                                    full_response += content
                        else:
                            print(f"⚠️ Skipping duplicate content: {content[:50]}{'...' if len(content) > 50 else ''}")
                
                # Check for tool results - this is the key addition
                if hasattr(last_message, 'tool_results') and last_message.tool_results:
                    print(f"🔧 Tool results found: {len(last_message.tool_results)}")
                    for tool_result in last_message.tool_results:
                        if isinstance(tool_result, dict):
                            # Check for content in tool result
                            for key, value in tool_result.items():
                                if key in ['content', 'output', 'result', 'data'] and value:
                                    content = str(value)
                                    if content and content.strip() and content.lower() != 'null':
                                        print(f"🔧 Tool result {key} found: {content[:100]}...")
                                        # Check if this is email content
                                        if _is_email_like_content(content):
                                            if not email_content_processed:
                                                print(f"🔧 Processing tool result email content: {content[:100]}...")
                                                formatted_content = _format_email_response(content)
                                                if formatted_content:
                                                    print(f"🔧 Adding formatted tool result email content: {formatted_content[:100]}...")
                                                    writer(formatted_content)
                                                    full_response += formatted_content
                                                    email_content_processed = True
                                                    print(f"📧 Processed tool result email content")
                                                else:
                                                    print(f"⚠️ Skipped duplicate tool result email content")
                                            else:
                                                print(f"⚠️ Skipping duplicate tool result email content")
                                        else:
                                            # Add non-email tool result content
                                            if content.strip().lower() != user_input.strip().lower():
                                                print(f"🔧 Adding tool result content: {content[:100]}...")
                                                writer(content)
                                                full_response += content
                                        break
                
                # Check for additional kwargs that might contain tool results
                if hasattr(last_message, 'additional_kwargs') and last_message.additional_kwargs:
                    if 'tool_results' in last_message.additional_kwargs:
                        tool_results = last_message.additional_kwargs['tool_results']
                        print(f"🔧 Tool results from kwargs: {len(tool_results)}")
                        for tool_result in tool_results:
                            if isinstance(tool_result, dict) and 'content' in tool_result:
                                content = tool_result['content']
                                if content and content.strip() and content.lower() != 'null':
                                    print(f"🔧 Tool result content from kwargs: {content[:100]}...")
                                    # Check if this is email content
                                    if _is_email_like_content(content):
                                        if not email_content_processed:
                                            print(f"🔧 Processing kwargs email content: {content[:100]}...")
                                            formatted_content = _format_email_response(content)
                                            if formatted_content:
                                                print(f"🔧 Adding formatted kwargs email content: {formatted_content[:100]}...")
                                                writer(formatted_content)
                                                full_response += formatted_content
                                                email_content_processed = True
                                                print(f"📧 Processed kwargs email content")
                                            else:
                                                print(f"⚠️ Skipped duplicate kwargs email content")
                                        else:
                                            print(f"⚠️ Skipping duplicate kwargs email content")
                                    else:
                                        # Add non-email kwargs content
                                        if content.strip().lower() != user_input.strip().lower():
                                            print(f"🔧 Adding kwargs content: {content[:100]}...")
                                            writer(content)
                                            full_response += content
                
                # Check for any other response format that might contain tool results
                if hasattr(last_message, '__dict__'):
                    for key, value in last_message.__dict__.items():
                        # Skip internal metadata fields
                        if key in ['content', 'tool_calls', 'tool_results', 'additional_kwargs', 'type', 'id', 'response_metadata', 'usage_metadata']:
                            continue
                        
                        if value and isinstance(value, str) and value.strip() and value.lower() != 'null':
                            # Skip internal IDs and metadata
                            if any(skip_pattern in key.lower() for skip_pattern in ['id', 'metadata', 'type', 'usage', 'response']):
                                continue
                            
                            print(f"🔧 Additional field {key}: {str(value)[:100]}...")
                            # Check if this is email content
                            if _is_email_like_content(value):
                                if not email_content_processed:
                                    print(f"🔧 Processing additional field email content: {value[:100]}...")
                                    formatted_content = _format_email_response(value)
                                    if formatted_content:
                                        print(f"🔧 Adding formatted additional field email content: {formatted_content[:100]}...")
                                        writer(formatted_content)
                                        full_response += formatted_content
                                        email_content_processed = True
                                        print(f"📧 Processed additional field email content")
                                    else:
                                        print(f"⚠️ Skipped duplicate additional field email content")
                                else:
                                    print(f"⚠️ Skipping duplicate additional field email content")
                            else:
                                # Add non-email additional field content
                                if value.strip().lower() != user_input.strip().lower():
                                    print(f"🔧 Adding additional field content: {value[:100]}...")
                                    writer(value)
                                    full_response += value
                
                # Check for tool execution results in the message - additional check
                if hasattr(last_message, 'tool_results') and last_message.tool_results:
                    for tool_result in last_message.tool_results:
                        if isinstance(tool_result, dict):
                            # Check for any content in the tool result
                            for key, value in tool_result.items():
                                if key in ['content', 'output', 'result', 'data'] and value:
                                    print(f"🔧 Tool result {key} found: {str(value)[:100]}...")
                                    content = str(value)
                                    if content and content.strip() and content.lower() != 'null':
                                        # Check if this is email content
                                        if _is_email_like_content(content):
                                            if not email_content_processed:
                                                print(f"🔧 Processing additional tool result email content: {content[:100]}...")
                                                formatted_content = _format_email_response(content)
                                                if formatted_content:
                                                    print(f"🔧 Adding formatted additional tool result email content: {formatted_content[:100]}...")
                                                    writer(formatted_content)
                                                    full_response += formatted_content
                                                    email_content_processed = True
                                                    print(f"📧 Processed additional tool result email content")
                                                else:
                                                    print(f"⚠️ Skipped duplicate additional tool result email content")
                                            else:
                                                print(f"⚠️ Skipping duplicate additional tool result email content")
                                        else:
                                            # Add non-email additional tool result content
                                            if content.strip().lower() != user_input.strip().lower():
                                                print(f"🔧 Adding additional tool result content: {content[:100]}...")
                                                writer(content)
                                                full_response += content
                                    break
                
                # Track tool calls for summary
                if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                    for tool_call in last_message.tool_calls:
                        tool_calls_made.append(tool_call)
                        print(f"🔧 Tool call detected: {tool_call.get('name', 'Unknown')}")
    
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        print(f"❌ Error during streaming: {e}")
        writer(error_msg)
        full_response += error_msg
    
    # If tool calls were made, provide summaries (even if content was already written)
    if tool_calls_made:
        print(f"🔧 {len(tool_calls_made)} tool calls were made, providing summaries...")
        summaries_provided = False
        for tool_call in tool_calls_made:
            tool_name = tool_call.get('name', 'Unknown')
            print(f"🔧 Processing tool call: {tool_name}")
            if tool_name == 'Gmail_WriteDraftEmail' and not summaries_provided:
                # Provide a summary of the draft email
                args = tool_call.get('args', {})
                subject = args.get('subject', 'No subject')
                recipient = args.get('recipient', 'No recipient')
                body = args.get('body', 'No body')
                
                # Check if we have the required arguments
                if not body or body == 'No body' or body.strip() == '' or not recipient or recipient == 'No recipient':
                    draft_summary = f"""⚠️ **Draft Email Creation Issue**

I attempted to create a draft email, but there might be an issue with the email content or recipient information.

**Details:**
- **Subject:** {subject}
- **Recipient:** {recipient}
- **Body:** {body[:100] if body and body != 'No body' else 'Empty or missing body content'}

**Possible Issues:**
1. The recipient email address might be invalid
2. The email content might be empty
3. The email subject might be missing

**To fix this:**
- Please provide a valid recipient email address
- Include meaningful email content in the body
- Make sure the subject line is not empty"""
                else:
                    draft_summary = f"""✅ **Draft Email Created Successfully!**

I've created a draft email for you with the following details:

**Subject:** {subject}
**Recipient:** {recipient}
**Body:** {body[:200]}{'...' if len(body) > 200 else ''}

**📍 Where to find your draft:**
- **Gmail Web Interface:** [Click here to open Gmail Drafts](https://mail.google.com/mail/u/0/#drafts)
- **Gmail Mobile App:** Open Gmail app → Tap the menu (☰) → Select "Drafts"
- **Gmail Desktop:** Look for "Drafts" in the left sidebar

The draft email has been saved to your Gmail drafts folder. You can review, edit, and send it when you're ready!

**💡 If you don't see the draft:**
1. **Refresh your Gmail drafts folder** - drafts sometimes take a moment to appear
2. **Check the "Drafts" folder** in the left sidebar of Gmail
3. **Ask me to "show me my drafts"** to list all your saved drafts
4. **Look for drafts with similar content** - the draft might have a different subject line"""
                
                writer(draft_summary)
                full_response += draft_summary
                print(f"📧 Added draft summary to response")
                summaries_provided = True
                break
            elif tool_name == 'Gmail_WriteDraftReplyEmail' and not summaries_provided:
                # Provide a summary of the draft reply email
                args = tool_call.get('args', {})
                subject = args.get('subject', 'No subject')
                recipient = args.get('recipient', 'No recipient')
                body = args.get('body', 'No body')
                
                # Check if we have the required arguments
                if not body or body == 'No body' or body.strip() == '':
                    draft_reply_summary = f"""⚠️ **Draft Reply Email Creation Issue**

I attempted to create a draft reply email, but there might be an issue with the email content.

**Details:**
- **Subject:** {subject}
- **Recipient:** {recipient}
- **Body:** {body[:100] if body and body != 'No body' else 'Empty or missing body content'}

**Possible Issues:**
1. The email content might be empty
2. The email subject might be missing
3. The recipient information might be incomplete

**To fix this:**
- Please provide meaningful email content in the body
- Make sure the subject line is not empty
- Ensure the recipient information is complete"""
                else:
                    draft_reply_summary = f"""✅ **Draft Reply Email Created Successfully!**

I've created a draft reply email for you with the following details:

**Subject:** {subject}
**Recipient:** {recipient}
**Body:** {body[:200]}{'...' if len(body) > 200 else ''}

**📍 Where to find your draft reply:**
- **Gmail Web Interface:** [Click here to open Gmail Drafts](https://mail.google.com/mail/u/0/#drafts)
- **Gmail Mobile App:** Open Gmail app → Tap the menu (☰) → Select "Drafts"
- **Gmail Desktop:** Look for "Drafts" in the left sidebar

The draft reply has been saved to your Gmail drafts folder. You can review, edit, and send it when you're ready!

**💡 If you don't see the draft:**
1. **Refresh your Gmail drafts folder** - drafts sometimes take a moment to appear
2. **Check the "Drafts" folder** in the left sidebar of Gmail
3. **Ask me to "show me my drafts"** to list all your saved drafts
4. **Look for drafts with similar content** - the draft might have a different subject line"""
                
                writer(draft_reply_summary)
                full_response += draft_reply_summary
                print(f"📧 Added draft reply summary to response")
                summaries_provided = True
                break
            elif tool_name == 'Gmail_ListDraftEmails' and not summaries_provided:
                # Provide a summary of draft listing
                draft_list_summary = f"""✅ **Draft Emails Retrieved!**

I've retrieved your draft emails. Check the results above to see all your saved drafts.

**📍 Access your drafts:**
- **Gmail Web Interface:** [Click here to open Gmail Drafts](https://mail.google.com/mail/u/0/#drafts)
- **Gmail Mobile App:** Open Gmail app → Tap the menu (☰) → Select "Drafts"
- **Gmail Desktop:** Look for "Drafts" in the left sidebar"""
                writer(draft_list_summary)
                full_response += draft_list_summary
                print(f"📧 Added draft list summary to response")
                summaries_provided = True
                break
            elif tool_name == 'Gmail_DeleteDraftEmail' and not summaries_provided:
                # Provide a summary of draft deletion
                draft_delete_summary = f"""✅ **Draft Email Deleted Successfully!**

I've deleted the specified draft email from your Gmail drafts folder."""
                writer(draft_delete_summary)
                full_response += draft_delete_summary
                print(f"📧 Added draft deletion summary to response")
                summaries_provided = True
                break
            elif tool_name == 'Gmail_SendDraftEmail' and not summaries_provided:
                # Provide a summary of draft sending
                draft_send_summary = f"""✅ **Draft Email Sent Successfully!**

I've sent the specified draft email. The email has been delivered to the recipient(s)."""
                writer(draft_send_summary)
                full_response += draft_send_summary
                print(f"📧 Added draft sending summary to response")
                summaries_provided = True
                break
            elif tool_name == 'Gmail_ListEmails' and not summaries_provided and not full_response.strip():
                # Only provide summary if no other content was written
                email_summary = f"""✅ **Email Search Completed!**

I've searched your emails using the criteria you specified. Check the results above for the emails I found."""
                writer(email_summary)
                full_response += email_summary
                print(f"📧 Added email search summary to response")
                summaries_provided = True
                break
    
    # Final check: if no content was found but tools were executed, try to get content from the final state
    if not full_response.strip() and tool_calls_made:
        print(f"🔍 No content found but tools were executed, checking final state...")
        try:
            # Get the final state from the graph
            final_state = graph.get_state(config)
            if final_state and hasattr(final_state, 'messages') and final_state.messages:
                print(f"🔍 Checking {len(final_state.messages)} messages in final state...")
                
                # Check the last few messages for content
                for message in reversed(final_state.messages[-3:]):
                    print(f"🔍 Checking message type: {type(message)}")
                    
                    # Check for AIMessage content (final response)
                    if hasattr(message, 'content') and message.content:
                        content = str(message.content)
                        if content and content.strip() and content.lower() != 'null':
                            print(f"🔍 Found final state content: {content[:100]}...")
                            if _is_email_like_content(content):
                                if not email_content_processed:
                                    formatted_content = _format_email_response(content)
                                    if formatted_content:
                                        writer(formatted_content)
                                        full_response += formatted_content
                                        email_content_processed = True
                                        print(f"📧 Processed final state email content")
                            else:
                                if content.strip().lower() != user_input.strip().lower():
                                    writer(content)
                                    full_response += content
                                    print(f"📧 Added final state content")
                            break
                    
                    # Check for ToolMessage content (tool results)
                    if hasattr(message, 'tool_results') and message.tool_results:
                        for tool_result in message.tool_results:
                            if isinstance(tool_result, dict):
                                for key, value in tool_result.items():
                                    if key in ['content', 'output', 'result', 'data'] and value:
                                        content = str(value)
                                        if content and content.strip() and content.lower() != 'null':
                                            print(f"🔍 Found final state tool result in {key}: {content[:100]}...")
                                            if _is_email_like_content(content):
                                                if not email_content_processed:
                                                    formatted_content = _format_email_response(content)
                                                    if formatted_content:
                                                        writer(formatted_content)
                                                        full_response += formatted_content
                                                        email_content_processed = True
                                                        print(f"📧 Processed final state tool result email content")
                                            else:
                                                if content.strip().lower() != user_input.strip().lower():
                                                    writer(content)
                                                    full_response += content
                                                    print(f"📧 Added final state tool result content")
                                            break
                                if full_response:
                                    break
                        if full_response:
                            break
        except Exception as e:
            print(f"🔍 Error checking final state: {e}")
    
    # Finalize the content display
    writer.finalize()
    
    print(f"✅ Streaming completed")
    print(f"📊 Final response length: {len(full_response)} characters")
    
    return full_response.strip()


def _is_email_like_content(content):
    """Check if content looks like email data."""
    if not content or not isinstance(content, str):
        return False
    
    # First, check if content is already formatted (contains HTML)
    if '<div' in content or '<span' in content:
        return False
    
    # Check if this is just a user query (not actual email data)
    normalized_content = content.strip().lower()
    user_query_indicators = [
        'show me', 'what emails', 'get emails', 'find emails', 'search for emails',
        'list emails', 'display emails', 'retrieve emails', 'draft a reply'
    ]
    
    # If it's a user query, don't treat it as email content
    if any(indicator in normalized_content for indicator in user_query_indicators):
        return False
    
    # Check for actual email data indicators - be more comprehensive
    email_indicators = [
        'emails":', 'subject:', 'from:', 'date:', 'to:', 
        'snippet:', 'full email:', 'thread_id', 'body', '{"emails"',
        'email_id', 'message_id', 'gmail_id', 'thread_id',
        'sender', 'recipient', 'cc:', 'bcc:', 'reply-to:',
        'content-type:', 'mime-version:', 'x-mailer:',
        'received:', 'return-path:', 'delivered-to:',
        'email', 'emails', 'message', 'messages'
    ]
    
    # Check for JSON structure that might contain email data
    if content.strip().startswith('{') and content.strip().endswith('}'):
        try:
            import json
            data = json.loads(content)
            # Check if it contains email-related keys
            if isinstance(data, dict):
                email_keys = ['emails', 'email', 'messages', 'message', 'threads', 'thread']
                if any(key in data for key in email_keys):
                    return True
                # Check if any value contains email-like data
                for value in data.values():
                    if isinstance(value, str) and any(indicator in value.lower() for indicator in email_indicators):
                        return True
        except (json.JSONDecodeError, Exception):
            pass
    
    # Check for email-like patterns in the content
    has_email_indicators = any(indicator in content.lower() for indicator in email_indicators)
    
    # Additional check: if it's a summary or description, don't treat as email content
    if 'here are' in normalized_content and 'emails' in normalized_content and len(content) < 200:
        return False
    
    # Check for email-like structure (subject, from, date patterns)
    email_structure_patterns = [
        r'subject\s*:', r'from\s*:', r'date\s*:', r'to\s*:',
        r'email\s*:', r'message\s*:', r'thread\s*:'
    ]
    
    import re
    has_email_structure = any(re.search(pattern, content, re.IGNORECASE) for pattern in email_structure_patterns)
    
    return has_email_indicators or has_email_structure


# Global variable to track processed emails across sessions
_processed_emails_global = set()
_processed_email_content_hashes = set()  # Track email content hashes
_processed_email_subjects = set()  # Track email subjects to prevent duplicates

def _format_email_response(content):
    """Format email response to match Arcade playground style."""
    global _processed_emails_global, _processed_email_subjects
    
    print(f"🔧 Formatting email response: {content[:200]}...")
    
    # Create a normalized version of the content for duplicate detection
    normalized_content = content.strip().lower()
    
    # Check if this is just a repetition of a user query
    if any(query in normalized_content for query in ['show me', 'what emails', 'get emails', 'find emails']):
        print(f"⚠️ Skipping user query repetition in email content: {content[:50]}...")
        return ""
    
    # Check if this is a summary or description (not actual email data)
    if 'here are' in normalized_content and 'emails' in normalized_content and len(content) < 200:
        print(f"⚠️ Skipping email summary/description: {content[:50]}...")
        return ""
    
    # Create a hash of the content to check for duplicates
    content_hash = hash(content.strip())
    if content_hash in _processed_email_content_hashes:
        print(f"⚠️ Skipping duplicate email content (hash: {content_hash})")
        return ""
    
    _processed_email_content_hashes.add(content_hash)
    
    try:
        # Try to parse as JSON first
        import json
        if content.strip().startswith('{') and content.strip().endswith('}'):
            print(f"🔧 Parsing as JSON: {content[:100]}...")
            data = json.loads(content)
            formatted = _format_json_email_data(data)
            print(f"🔧 JSON formatting result: {formatted[:100]}...")
            return formatted
        
        # If not JSON, try to format as plain text email
        print(f"🔧 Parsing as plain text email")
        formatted = _format_plain_text_email(content)
        print(f"🔧 Plain text formatting result: {formatted[:100]}...")
        return formatted
    except (json.JSONDecodeError, Exception) as e:
        print(f"⚠️ Could not parse as JSON, formatting as plain text: {e}")
        return _format_plain_text_email(content)

def _format_json_email_data(data):
    """Format JSON email data to match Arcade playground style."""
    global _processed_emails_global, _processed_email_subjects
    formatted_content = ""
    
    print(f"🔧 Formatting JSON email data: {str(data)[:200]}...")
    
    if 'emails' in data and isinstance(data['emails'], list):
        print(f"🔧 Found {len(data['emails'])} emails in data")
        formatted_content += f"**Here are the emails from {data.get('from', 'your inbox')}:**\n\n"
        
        # Track which emails we've already processed in this session
        processed_in_session = set()
        email_count = 0  # Track actual emails added (not skipped)
        
        for i, email in enumerate(data['emails'], 1):
            print(f"🔧 Processing email {i}: {email.get('subject', 'No subject')[:50]}...")
            
            # Create a unique identifier for this email
            email_id = f"{email.get('subject', '')}_{email.get('date', '')}_{email.get('snippet', '')[:50]}"
            email_subject = email.get('subject', '').strip()
            
            # Check for duplicates using multiple criteria
            is_duplicate = False
            
            # Check global email ID tracking
            if email_id in _processed_emails_global:
                print(f"⚠️ Skipping duplicate email (global ID): {email.get('subject', 'No subject')}")
                is_duplicate = True
            
            # Check session-level email ID tracking
            elif email_id in processed_in_session:
                print(f"⚠️ Skipping duplicate email (session ID): {email.get('subject', 'No subject')}")
                is_duplicate = True
            
            # Check subject tracking (additional safety)
            elif email_subject and email_subject in _processed_email_subjects:
                print(f"⚠️ Skipping duplicate email (subject): {email_subject}")
                is_duplicate = True
            
            if is_duplicate:
                continue
            
            # Add to tracking sets
            _processed_emails_global.add(email_id)
            processed_in_session.add(email_id)
            if email_subject:
                _processed_email_subjects.add(email_subject)
            
            email_count += 1
            
            formatted_content += f'<div class="email-content" style="color: #212529;">\n'
            formatted_content += f'<div class="email-header" style="color: #212529;">\n'
            
            # Add subject if available
            if 'subject' in email and email['subject']:
                formatted_content += f'<div class="email-subject" style="color: #495057;">**{email_count}. Subject: {email["subject"]}**</div>\n'
            else:
                formatted_content += f'<div class="email-subject" style="color: #495057;">**{email_count}. Email**</div>\n'
            
            # Add date if available
            if 'date' in email and email['date']:
                formatted_content += f'<div class="email-meta" style="color: #6c757d;">**Date:** {email["date"]}</div>\n'
            
            formatted_content += '</div>\n'
            
            # Add snippet if available
            if 'snippet' in email and email['snippet']:
                formatted_content += f'<div class="email-snippet" style="color: #495057;">**Snippet:** {email["snippet"]}</div>\n'
            
            # Add full email body if available
            if 'body' in email and email['body']:
                formatted_content += f'<div class="email-body" style="color: #212529;">**Full Email:**\n{email["body"]}</div>\n'
            
            formatted_content += '</div>\n\n'
        
        print(f"🔧 Added {email_count} unique emails out of {len(data['emails'])} total emails")
    else:
        print(f"⚠️ No 'emails' key found in data or emails is not a list: {list(data.keys()) if isinstance(data, dict) else type(data)}")
    
    print(f"🔧 Final formatted content length: {len(formatted_content)}")
    return formatted_content


def _format_plain_text_email(content):
    """Format plain text email content."""
    lines = content.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line or line.lower() == 'null':
            continue
        
        # Format common email patterns
        if line.lower().startswith('subject:'):
            formatted_lines.append(f'<div class="email-subject" style="color: #495057;">**{line}**</div>')
        elif line.lower().startswith('from:'):
            formatted_lines.append(f'<div class="email-meta" style="color: #6c757d;">**{line}**</div>')
        elif line.lower().startswith('date:'):
            formatted_lines.append(f'<div class="email-meta" style="color: #6c757d;">**{line}**</div>')
        elif line.lower().startswith('to:'):
            formatted_lines.append(f'<div class="email-meta" style="color: #6c757d;">**{line}**</div>')
        elif line.lower().startswith('snippet:'):
            formatted_lines.append(f'<div class="email-snippet" style="color: #495057;">**{line}**</div>')
        elif line.lower().startswith('full email:'):
            formatted_lines.append(f'<div class="email-body" style="color: #212529;">**{line}**</div>')
        else:
            formatted_lines.append(f'<div style="color: #212529;">{line}</div>')
    
    return '\n'.join(formatted_lines)

async def run_agent_interaction(user_input: str, user_email: str, thread_id: str):
    """Run the agent interaction with proper error handling."""
    print(f"🎯 Starting agent interaction for user: {user_email}")
    print(f"🆔 Thread ID: {thread_id[:8]}...")
    
    # Format user_id (remove dots for consistency) - ensure user_email is a string
    if hasattr(user_email, 'email'):
        # If user_email is a User object, extract the email
        user_email = user_email.email
    
    user_id = user_email.replace(".", "")
    print(f"👤 Formatted user_id: {user_id}")
    
    # Prepare agent config (matching official documentation)
    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": user_id
        }
    }
    print(f"⚙️ Agent config: {config}")
    
    # Create a placeholder for streaming
    placeholder = st.empty()
    print(f"📝 Created response placeholder for streaming")
    
    try:
        # Build the graph (simplified)
        print(f"🔧 Building LangGraph...")
        graph = build_graph()
        print(f"✅ LangGraph built successfully")
        
        # Start streaming the response (synchronous call)
        print(f"🚀 Starting response streaming...")
        response = stream_agent_response(user_input, graph, config, placeholder)
        print(f"🎉 Agent interaction completed. Response length: {len(response)} characters")
        
        return response
        
    except Exception as e:
        error_msg = f"Error during agent interaction: {str(e)}"
        print(f"❌ {error_msg}")
        placeholder.error(error_msg)
        return error_msg

# Sidebar for authentication
with st.sidebar:
    st.title("🎮 Arcade AI Agent")
    
    if not st.session_state.authenticated:
        print("🔒 Showing authentication tabs - user not logged in")
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            st.subheader("Login")
            login_email = st.text_input("Email", key="login_email")
            login_password = st.text_input("Password", type="password", key="login_password")
            login_button = st.button("Login")
            
            if login_button:
                print(f"🔐 Login button clicked for email: {login_email}")
                if login_email and login_password:
                    sign_in(login_email, login_password)
                else:
                    print("⚠️ Login attempt with missing credentials")
                    st.warning("Please enter both email and password.")
        
        with tab2:
            st.subheader("Sign Up")
            signup_email = st.text_input("Email", key="signup_email")
            signup_password = st.text_input("Password", type="password", key="signup_password")
            signup_name = st.text_input("Full Name", key="signup_name")
            signup_button = st.button("Sign Up")
            
            if signup_button:
                print(f"📝 Sign up button clicked for email: {signup_email}, name: {signup_name}")
                if signup_email and signup_password and signup_name:
                    response = sign_up(signup_email, signup_password, signup_name)
                    if response and response.user:
                        print("✅ Sign up successful - showing success message")
                        st.success("Sign up successful! Please check your email to confirm your account.")
                    else:
                        print("❌ Sign up failed - showing error message")
                        st.error("Sign up failed. Please try again.")
                else:
                    print("⚠️ Sign up attempt with missing fields")
                    st.warning("Please fill in all fields.")
    else:
        user = st.session_state.user
        if user:
            # Handle User object properly
            user_email = user.email if hasattr(user, 'email') else str(user)
            print(f"✅ User authenticated in sidebar: {user_email}")
            st.success(f"Logged in as: {user_email}")
            
            logout_button = st.button("Logout")
            if logout_button:
                print("🚪 Logout button clicked")
                sign_out()
            
            # Display session information
            st.divider()
            st.subheader("Session Info")
            st.text(f"Thread ID: {st.session_state.thread_id[:8]}...")
            st.text(f"Messages: {len(st.session_state.messages)}")
            
            # Show storage status
            if database_url:
                st.success("🗄️ Using PostgreSQL Database")
            else:
                st.warning("💾 Using In-Memory Storage")
                st.caption("(Memory will be lost on restart)")
            
            # Clear conversation button
            clear_button = st.button("🔄 New Conversation")
            if clear_button:
                print("🔄 New conversation button clicked - clearing messages and generating new thread")
                st.session_state.messages = []
                st.session_state.thread_id = str(uuid.uuid4())
                # Clear the global processed emails set
                clear_processed_emails()
                print(f"🆔 New thread ID generated: {st.session_state.thread_id[:8]}...")
                st.rerun()
            
            # Clean error messages button
            clean_button = st.button("🧹 Clean Errors")
            if clean_button:
                print("🧹 Clean errors button clicked")
                # Remove error messages from history
                st.session_state.messages = [
                    msg for msg in st.session_state.messages 
                    if not (msg["role"] == "assistant" and "Error processing request" in msg["content"])
                ]
                print(f"🧹 Cleaned conversation - {len(st.session_state.messages)} messages remaining")
                st.rerun()
            
            # Instructions
            st.divider()
            st.markdown("""
            ### 💡 How to Use
            
            **Email Commands:**
            - "What emails do I have?"
            - "Show me emails from today"
            - "Search for emails about meetings"
            
            **Memory Features:**
            - Include "remember" in your message to store information
            - The agent will recall relevant memories automatically
            
            **Web Scraping:**
            - "Scrape this URL: [website]"
            - "Get information from [website]"
            
            The agent has access to Gmail and web scraping tools.
            """)

# Main chat interface
if st.session_state.authenticated:
    st.title("🎮 Arcade AI Agent Chat")
    st.markdown("AI assistant with email access, web scraping, and memory capabilities")
    
    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.markdown(message["content"])
        elif message["role"] == "assistant":
            with st.chat_message("assistant"):
                # Check if this is email content and format it properly
                content = message["content"]
                print(f"content :{content}")
                # Check if content is already formatted (contains HTML)
                if '<div' in content or '<span' in content:
                    # Content is already formatted, display as is
                    st.markdown(content, unsafe_allow_html=True)
                elif _is_email_like_content(content):
                    # Format email content for display
                    formatted_content = _format_email_response(content)
                    st.markdown(formatted_content, unsafe_allow_html=True)
                else:
                    st.markdown(content)
    
    # Chat input
    if prompt := st.chat_input("Ask me anything..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Display assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            # Process the message - handle User object properly
            user_email = st.session_state.user.email if hasattr(st.session_state.user, 'email') else str(st.session_state.user)
            response = asyncio.run(run_agent_interaction(prompt, user_email, st.session_state.thread_id))
            
            # Check if response is already formatted (contains HTML)
            if '<div' in response or '<span' in response:
                # Response is already formatted, display as is
                message_placeholder.markdown(response, unsafe_allow_html=True)
            elif _is_email_like_content(response):
                # Format email content for display
                formatted_response = _format_email_response(response)
                message_placeholder.markdown(formatted_response, unsafe_allow_html=True)
            else:
                message_placeholder.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
else:
    print("🔒 User not authenticated - showing welcome screen")
    # Welcome screen for non-authenticated users
    st.title("Welcome to Arcade AI Agent")
    st.write("Please login or sign up to start chatting with the AI assistant.")
    st.write("This AI agent can:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📧 Email Access")
        st.write("Read and search through your Gmail inbox")
    
    with col2:
        st.markdown("### 🌐 Web Scraping")
        st.write("Extract information from websites")
    
    with col3:
        st.markdown("### 🧠 Memory")
        st.write("Remember important information across conversations")
    
    st.markdown("""
    <div class="auth-message">
    <strong>Note:</strong> You'll need to authorize Gmail access when first using email features.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    # This won't run in Streamlit, but kept for consistency
    pass

print("🎉 Streamlit app initialization complete!")
print("=" * 50)