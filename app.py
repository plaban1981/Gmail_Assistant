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
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore

# Import our agent
from arcade_3_agent_with_memory import build_graph

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL", "")
supabase_key = os.environ.get("SUPABASE_KEY", "")
supabase_client = supabase.create_client(supabase_url, supabase_key)

# Get other environment variables
arcade_api_key = os.environ.get("ARCADE_API_KEY")
openai_api_key = os.environ.get("OPENAI_API_KEY")
model_choice = os.environ.get("MODEL_CHOICE")
database_url = os.environ.get("DATABASE_URL")

# Streamlit page configuration
st.set_page_config(
    page_title="Arcade AI Agent",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better formatting
st.markdown("""
<style>
    .stMarkdown h3 {
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        color: #1f77b4;
    }
    .auth-message {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    .main-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-container {
        max-width: 900px;
        margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True)

# Authentication functions
def sign_up(email, password, full_name):
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
            st.session_state.authenticated = True
            st.session_state.user = response.user
            st.rerun()
        return response
    except Exception as e:
        st.error(f"Error signing up: {str(e)}")
        return None

def sign_in(email, password):
    try:
        response = supabase_client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if response and response.user:
            # Store user info directly in session state
            st.session_state.authenticated = True
            st.session_state.user = response.user
            st.rerun()
        return response
    except Exception as e:
        st.error(f"Error signing in: {str(e)}")
        return None

def sign_out():
    try:
        supabase_client.auth.sign_out()
        # Clear authentication-related session state
        st.session_state.authenticated = False
        st.session_state.user = None
        # Clear conversation history
        st.session_state.messages = []
        # Generate new thread ID for next session
        st.session_state.thread_id = str(uuid.uuid4())
        # Set a flag to trigger rerun on next render
        st.session_state.logout_requested = True
    except Exception as e:
        st.error(f"Error signing out: {str(e)}")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# Check for logout flag and clear it after processing
if st.session_state.get("logout_requested", False):
    st.session_state.logout_requested = False
    st.rerun()

# Custom writer function for streaming
class StreamlitWriter:
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.content = ""
    
    def __call__(self, text):
        # Add proper formatting for authorization messages
        if "🔐 Authorization required" in text:
            # Add newlines around authorization messages
            if not self.content.endswith("\n"):
                self.content += "\n"
            self.content += text
            if not text.endswith("\n"):
                self.content += "\n"
        elif "Visit the following URL to authorize:" in text:
            # Add newline before and after URL instruction
            if not self.content.endswith("\n"):
                self.content += "\n"
            self.content += text + "\n"
        elif "Waiting for authorization..." in text:
            # Add newlines around waiting message
            if not self.content.endswith("\n"):
                self.content += "\n"
            self.content += text + "\n\n"
        elif text.startswith("You have the following emails") or text.startswith("From "):
            # Add newline before email content
            if not self.content.endswith("\n"):
                self.content += "\n"
            self.content += text
        else:
            self.content += text
        
        self.placeholder.markdown(self.content)

async def stream_agent_response(user_input: str, graph, config: dict, placeholder):
    """Stream agent response with proper handling."""
    
    # Build conversation history
    messages = []
    
    # Add conversation history
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))
    
    # Add current user message
    messages.append(HumanMessage(content=user_input))
    
    # Prepare input
    inputs = {
        "messages": messages
    }
    
    writer = StreamlitWriter(placeholder)
    full_response = ""
    processed_content = set()
    email_content_processed = False
    
    try:
        # Stream the response
        async for chunk in graph.astream(inputs, config=config, stream_mode="values"):
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
                
                # Check for tool calls - if tools were called, provide feedback
                if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                    print(f"🔧 Tool calls found: {len(last_message.tool_calls)}")
                    for tool_call in last_message.tool_calls:
                        tool_name = tool_call.get('name', '')
                        tool_args = tool_call.get('args', {})
                        print(f"🔧 Tool call: {tool_name} with args: {tool_args}")
                        
                        # Provide user feedback for draft email tools
                        if tool_name == 'Gmail_WriteDraftEmail':
                            subject = tool_args.get('subject', 'No subject')
                            recipient = tool_args.get('recipient', 'No recipient')
                            body = tool_args.get('body', 'No body')
                            
                            draft_summary = f"""✅ **Draft Email Created Successfully!**

**📧 Draft Details:**
- **To**: {recipient}
- **Subject**: {subject}

**📝 Complete Draft Content:**
```
{body}
```

**✅ What happened:**
- Your draft email has been created and saved to your Gmail drafts folder
- You can access it at: https://mail.google.com/mail/u/0/#drafts
- You can edit, customize, and send it directly from Gmail

**📝 Next steps:**
1. Go to Gmail Drafts to review your email
2. Make any edits if needed
3. Send when ready!"""
                            
                            print(f"🔧 Adding draft email summary")
                            writer(draft_summary)
                            full_response += draft_summary
                            break
                            
                        elif tool_name == 'Gmail_WriteDraftReplyEmail':
                            subject = tool_args.get('subject', 'No subject')
                            recipient = tool_args.get('recipient', 'No recipient')
                            body = tool_args.get('body', 'No body')
                            reply_to_id = tool_args.get('reply_to_message_id', 'Unknown')
                            
                            draft_reply_summary = f"""✅ **Draft Reply Created Successfully!**

**📧 Draft Reply Details:**
- **To**: {recipient}
- **Subject**: {subject}
- **Replying to Message ID**: {reply_to_id}

**📝 Complete Draft Reply Content:**
```
{body}
```

**✅ What happened:**
- Your draft reply has been created and saved to your Gmail drafts folder
- You can access it at: https://mail.google.com/mail/u/0/#drafts
- You can edit, customize, and send it directly from Gmail

**📝 Next steps:**
1. Go to Gmail Drafts to review your reply
2. Make any edits if needed
3. Send when ready!"""
                            
                            print(f"🔧 Adding draft reply summary")
                            writer(draft_reply_summary)
                            full_response += draft_reply_summary
                            break
                
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
        
        return full_response
        
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        writer(error_msg)
        return error_msg

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

def _format_email_response(content):
    """Format email response to match Arcade playground style."""
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
    """Format JSON email data in simple list format."""
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
            
            # Check session-level email ID tracking
            if email_id in processed_in_session:
                print(f"⚠️ Skipping duplicate email (session ID): {email.get('subject', 'No subject')}")
                is_duplicate = True
            
            if is_duplicate:
                continue
            
            # Add to tracking sets
            processed_in_session.add(email_id)
            
            email_count += 1
            
            # Format email in simple format with content
            subject = email.get('subject', 'No subject')
            from_name = email.get('from_name', email.get('from', 'Unknown'))
            from_email = email.get('from_email', email.get('from', 'unknown@example.com'))
            
            # Clean up the from_email if it's in angle brackets
            if '<' in from_email and '>' in from_email:
                from_email = from_email.strip('<>')
            
            # Format as simple text with subject and sender
            formatted_content += f"{email_count}. Subject: \"{subject}\" from {from_name} ({from_email})\n"
            
            # Add email content/body if available
            if 'body' in email and email['body']:
                # Truncate very long emails for readability
                body = email['body']
                if len(body) > 500:
                    body = body[:500] + "...\n[Content truncated - full email content available]"
                formatted_content += f"   Content: {body}\n"
            elif 'snippet' in email and email['snippet']:
                formatted_content += f"   Preview: {email['snippet']}\n"
            
            formatted_content += "\n"  # Add extra line between emails
        
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
        if line and line.lower() != 'null':
            formatted_lines.append(line)
    
    # Rejoin with proper spacing
    formatted_content = '\n\n'.join(formatted_lines)
    return formatted_content

async def run_agent_interaction(user_input: str, user_email: str, thread_id: str):
    """Run the agent interaction with proper setup."""
    
    # Set up configuration
    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": user_email
        },
        "recursion_limit": 100
    }
    
    # Create placeholder for streaming
    response_placeholder = st.empty()
    
    # Use context managers for store and checkpointer
    async with (
        AsyncPostgresStore.from_conn_string(database_url) as store,
        AsyncPostgresSaver.from_conn_string(database_url) as checkpointer,
    ):
        # Build the graph
        graph = build_graph()
        
        # Stream the response
        response = await stream_agent_response(
            user_input, 
            graph, 
            config, 
            response_placeholder
        )
        
        return response

# Sidebar for authentication
with st.sidebar:
    st.title("🎮 Arcade AI Agent")
    
    if not st.session_state.authenticated:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            st.subheader("Login")
            login_email = st.text_input("Email", key="login_email")
            login_password = st.text_input("Password", type="password", key="login_password")
            login_button = st.button("Login")
            
            if login_button:
                if login_email and login_password:
                    sign_in(login_email, login_password)
                else:
                    st.warning("Please enter both email and password.")
        
        with tab2:
            st.subheader("Sign Up")
            signup_email = st.text_input("Email", key="signup_email")
            signup_password = st.text_input("Password", type="password", key="signup_password")
            signup_name = st.text_input("Full Name", key="signup_name")
            signup_button = st.button("Sign Up")
            
            if signup_button:
                if signup_email and signup_password and signup_name:
                    response = sign_up(signup_email, signup_password, signup_name)
                    if response and response.user:
                        st.success("Sign up successful! Please check your email to confirm your account.")
                    else:
                        st.error("Sign up failed. Please try again.")
                else:
                    st.warning("Please fill in all fields.")
    else:
        user = st.session_state.user
        if user:
            st.success(f"Logged in as: {user.email}")
            st.button("Logout", on_click=sign_out)
            
            # Display session information
            st.divider()
            st.subheader("Session Info")
            st.text(f"Thread ID: {st.session_state.thread_id[:8]}...")
            st.text(f"Messages: {len(st.session_state.messages)}")
            
            # Clear conversation button
            if st.button("🔄 New Conversation"):
                st.session_state.messages = []
                st.session_state.thread_id = str(uuid.uuid4())
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
if st.session_state.authenticated and st.session_state.user:
    # Header
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.title("🎮 Arcade AI Agent Chat")
    st.markdown("AI assistant with email access, web scraping, and memory capabilities")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display all messages from conversation history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input (naturally appears at bottom)
    if prompt := st.chat_input("Ask me anything..."):
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Display assistant response
        with st.chat_message("assistant"):
            try:
                # Handle Windows event loop
                if sys.platform == 'win32':
                    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                
                # Run the async agent interaction
                response = asyncio.run(
                    run_agent_interaction(
                        prompt,
                        st.session_state.user.email,
                        st.session_state.thread_id
                    )
                )
                
                # Add both messages to chat history
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                # Still add the user message and error to history
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
else:
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