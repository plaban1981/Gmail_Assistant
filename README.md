# AI-Powered Email Assistant with Streamlit, LangGraph, and Arcade AI

## 📋 Table of Contents

- [Introduction](#introduction)
- [Project Overview](#project-overview)
- [Technology Stack](#technology-stack)
- [Installation & Setup](#installation--setup)
- [Architecture & Implementation](#architecture--implementation)
- [Key Features](#key-features)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Introduction

This project implements a sophisticated AI-powered email assistant that can read, search, and manage Gmail emails using modern AI technologies. The application combines the power of LangGraph for workflow orchestration, Streamlit for the user interface, and Arcade AI for Gmail integration.

## 🏗️ Project Overview

The **Gmail AI Assistant** allows users to:
- Search and read emails using natural language queries
- Draft and send emails through AI assistance
- Manage email labels and organization
- Maintain conversation memory across sessions
- Provide a clean, professional user interface

### Key Capabilities
- ✅ **Natural Language Email Search** - "Show me emails from LinkedIn"
- ✅ **Email Drafting** - "Draft a reply to the latest email"
- ✅ **Email Analysis** - "Summarize my emails from this week"
- ✅ **Conversation Memory** - Maintains context across sessions
- ✅ **Professional UI** - Clean, modern interface with light mode
- ✅ **Duplicate Prevention** - Smart content deduplication
- ✅ **Real-time Streaming** - Live content updates during processing

## 🛠️ Technology Stack

### Core Technologies
- **Python 3.8+** - Primary programming language
- **Streamlit** - Web application framework for the UI
- **LangGraph** - Workflow orchestration and state management
- **LangChain** - LLM framework and tool integration
- **Arcade AI** - Gmail API integration and tool management

### AI & ML
- **OpenAI GPT-4** - Large language model for natural language processing
- **LangChain Core** - Message handling and tool execution
- **LangGraph** - Multi-actor application framework

### Database & Storage
- **PostgreSQL** - Persistent conversation storage and checkpoints
- **Supabase** - Authentication and user management
- **LangGraph Checkpoints** - State persistence and conversation memory

### Authentication & Security
- **Supabase Auth** - User authentication and session management
- **OAuth 2.0** - Gmail API authorization
- **Environment Variables** - Secure API key management

## 🚀 Installation & Setup

### Prerequisites

```bash
# Python 3.8+ required
python --version

# Git for version control
git --version

# PostgreSQL database (optional, can use in-memory storage)
```

### 1. Clone the Repository

```bash
git clone <repository-url>
cd arcade-ai-assistant
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
MODEL_CHOICE=gpt-4o-mini

# Arcade AI Configuration
ARCADE_API_KEY=your_arcade_api_key_here

# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here

# Database Configuration (Optional)
DATABASE_URL=your_postgresql_url_here

# Application Configuration
EMAIL=your_email@example.com
```

### 4. Database Setup (Optional)

```sql
-- Create PostgreSQL database
CREATE DATABASE arcade_ai_assistant;

-- Tables will be created automatically by LangGraph
```

## 🏗️ Architecture & Implementation

### 1. Core Architecture

The application follows a **multi-layered architecture**:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   LangGraph     │    │   Arcade AI     │
│   (Frontend)    │◄──►│   (Workflow)    │◄──►│   (Gmail Tools) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│   PostgreSQL    │◄─────────────┘
                        │   (Storage)     │
                        └─────────────────┘
```

### 2. Key Components

#### A. Streamlit User Interface (`arcade_3_streamlit_app.py`)

**Features:**
- Clean, modern UI with light mode styling
- Real-time chat interface
- Email content formatting and display
- User authentication and session management
- Duplicate content detection and prevention

**Key Implementation Details:**

```python
# Light mode CSS styling
st.markdown("""
<style>
/* Force light mode throughout the app */
[data-testid="stAppViewContainer"] { background-color: #ffffff !important; }
[data-testid="stSidebar"] { background-color: #f0f2f6 !important; }
.main .block-container { background-color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# Email content formatting
def _format_email_response(content):
    """Format email response to match Arcade playground style."""
    global _processed_emails_global, _processed_email_content_hashes
    
    # Duplicate detection
    content_hash = hash(content.strip())
    if content_hash in _processed_email_content_hashes:
        return ""
    
    # Format email content with HTML styling
    formatted_content = f"""
    <div class="email-content" style="color: #212529;">
        <div class="email-header">
            <div class="email-subject">**{subject}**</div>
            <div class="email-meta">**Date:** {date}</div>
        </div>
        <div class="email-body">{body}</div>
    </div>
    """
    return formatted_content
```

#### B. LangGraph Workflow (`arcade_3_agent_with_memory.py`)

**Features:**
- Multi-actor workflow orchestration
- Tool execution and management
- Conversation memory and state persistence
- Authorization handling

**Key Implementation Details:**

```python
def build_graph():
    """Build the LangGraph workflow with memory."""
    workflow = StateGraph(MessagesState)
    
    # Add nodes
    workflow.add_node("agent", call_agent)
    workflow.add_node("tools", tool_node)
    workflow.add_node("authorization", authorize)
    
    # Define edges
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, 
                                 ["authorization", "tools", END])
    workflow.add_edge("authorization", "tools")
    workflow.add_edge("tools", "agent")
    
    # Compile with memory
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)

def call_agent(state: MessagesState):
    """Invoke the model and get a response."""
    messages = state["messages"]
    
    # Add system message for guidance
    system_message = """You are a helpful AI assistant with access to Gmail tools.
    When users ask about emails, you MUST use the Gmail tools to retrieve actual email data.
    
    Available Gmail tools:
    - Gmail_ListEmails: List emails from inbox with search criteria
    - Gmail_GetEmail: Get specific email by ID
    - Gmail_WriteDraftEmail: Create a draft email
    
    IMPORTANT: Always use the tools to retrieve actual email data and provide informative responses."""
    
    messages_with_system = [SystemMessage(content=system_message)] + messages
    response = model_with_tools.invoke(messages_with_system)
    
    return {"messages": [response]}
```

#### C. Email Content Processing

**Features:**
- JSON email data parsing and formatting
- Duplicate content detection and prevention
- Professional email display formatting
- Content streaming and real-time updates

**Key Implementation Details:**

```python
class StreamlitWriter:
    """Custom writer for streaming content to Streamlit."""
    
    def __init__(self, placeholder):
        self.placeholder = placeholder
        self.content = ""
        self.processed_content_hashes = set()
        self.finalized = False
    
    def __call__(self, text):
        # Duplicate detection
        content_hash = hash(text.strip())
        if content_hash in self.processed_content_hashes:
            return
        
        self.processed_content_hashes.add(content_hash)
        
        # Content processing
        if '<div' in text or '<span' in text:
            # Already formatted content
            if not self._is_duplicate_content(text):
                self.content += text
        elif self._is_email_content(text):
            # Email content formatting
            if not self.email_content_processed:
                formatted_text = self._format_email_content(text)
                if not self._is_duplicate_content(formatted_text):
                    self.content += formatted_text
                    self.email_content_processed = True
    
    def finalize(self):
        """Finalize content display once."""
        if not self.content.strip() or self.finalized:
            return
        
        self.finalized = True
        self.placeholder.markdown(self.content, unsafe_allow_html=True)
```

### 3. Data Flow

```
1. User Input → Streamlit UI
2. Streamlit UI → LangGraph Workflow
3. LangGraph → Arcade AI Tools
4. Arcade AI → Gmail API
5. Gmail API → Email Data
6. Email Data → LangGraph Processing
7. LangGraph → Streamlit Display
8. Streamlit → User Interface
```

## 🎯 Key Features & Implementation

### 1. Email Search & Display

**Natural Language Queries:**
```python
# User can ask questions like:
"Show me emails from today"
"Find emails about meetings"
"List emails from LinkedIn"
"Draft a reply to the latest email"
```

**Email Formatting:**
```python
def _format_json_email_data(data):
    """Format JSON email data to match Arcade playground style."""
    formatted_content = ""
    
    if 'emails' in data and isinstance(data['emails'], list):
        formatted_content += f"**Here are the emails from {data.get('from', 'your inbox')}:**\n\n"
        
        for i, email in enumerate(data['emails'], 1):
            formatted_content += f"""
            <div class="email-content" style="color: #212529;">
                <div class="email-header">
                    <div class="email-subject">**{i}. Subject: {email.get('subject', 'No subject')}**</div>
                    <div class="email-meta">**Date:** {email.get('date', 'No date')}</div>
                </div>
                <div class="email-snippet">**Snippet:** {email.get('snippet', 'No snippet')}</div>
                <div class="email-body">**Full Email:**\n{email.get('body', 'No body')}</div>
            </div>
            """
    
    return formatted_content
```

### 2. Duplicate Content Prevention

**Multi-Level Detection:**
```python
# Global tracking
_processed_emails_global = set()
_processed_email_content_hashes = set()
_processed_email_subjects = set()

# Content hash tracking
def _is_duplicate_content(self, content):
    content_hash = hash(content.strip())
    if content_hash in self.processed_emails:
        return True
    self.processed_emails.add(content_hash)
    return False
```

### 3. Authentication & Authorization

**Supabase Integration:**
```python
def sign_in(email, password):
    """Sign in user with Supabase."""
    try:
        response = supabase_client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        if response.user:
            st.session_state.authenticated = True
            st.session_state.user = response.user
            return response
    except Exception as e:
        print(f"❌ Error during sign in for {email}: {e}")
        return None
```

**Gmail Authorization:**
```python
def authorize(state: MessagesState, config: RunnableConfig):
    """Handle Gmail authorization."""
    user_id = config["configurable"].get("user_id")
    
    for tool_call in state["messages"][-1].tool_calls:
        tool_name = tool_call["name"]
        if manager.requires_auth(tool_name):
            auth_response = manager.authorize(tool_name, user_id)
            if auth_response.status != "completed":
                return {"messages": [AIMessage(content=f"Authorization required for {tool_name}")]}
    
    return {"messages": []}
```

## 🚀 Running the Application

### 1. Start the Application

```bash
# Activate virtual environment
source venv/bin/activate

# Run Streamlit app
streamlit run arcade_3_streamlit_app.py
```

### 2. Access the Application

- **Local URL:** http://localhost:8501
- **Network URL:** http://your-ip:8501

### 3. First-Time Setup

1. **Sign up/Sign in** using your email
2. **Authorize Gmail access** when prompted
3. **Start chatting** with the AI assistant

## 🎯 Use Cases & Examples

### 1. Email Search

```
User: "Show me emails from LinkedIn"
AI: [Displays formatted LinkedIn emails with subjects, dates, and snippets]
```

### 2. Email Drafting

```
User: "Draft a reply to the latest email"
AI: [Creates a draft email with appropriate subject, body, and recipient]
```

### 3. Email Management

```
User: "Find emails about meetings from this week"
AI: [Searches and displays relevant emails with meeting information]
```

## 🔍 Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Ensure Supabase credentials are correct
   - Check Gmail authorization status
   - Verify API keys in `.env` file

2. **Duplicate Content**
   - Clear browser cache
   - Reset conversation history
   - Check for multiple Streamlit instances

3. **Performance Issues**
   - Use in-memory storage for development
   - Optimize database queries
   - Monitor API rate limits

## 🎯 Main Objectives Behind Using LangGraph with Arcade AI

### 1. **Multi-Actor Workflow Orchestration**

**Objective:** Create a sophisticated, stateful workflow that can handle complex email management tasks with multiple AI agents and tools.

**Why LangGraph:**
- **State Management**: LangGraph provides built-in state management for maintaining conversation context and user sessions
- **Multi-Actor Architecture**: Supports multiple AI agents working together (email search, drafting, analysis)
- **Workflow Control**: Enables conditional routing and decision-making based on user requests

```python
# Example: Multi-actor workflow
def build_graph():
    workflow = StateGraph(MessagesState)
    
    # Multiple specialized nodes
    workflow.add_node("agent", call_agent)           # Main AI agent
    workflow.add_node("tools", tool_node)            # Tool execution
    workflow.add_node("authorization", authorize)    # Auth handling
    
    # Conditional routing
    workflow.add_conditional_edges("agent", should_continue, 
                                 ["authorization", "tools", END])
```

### 2. **Seamless Tool Integration with Arcade AI**

**Objective:** Integrate Gmail tools from Arcade AI into a conversational AI workflow without manual API management.

**Why LangGraph + Arcade:**
- **Tool Abstraction**: Arcade AI provides pre-built Gmail tools that LangGraph can execute
- **Automatic Tool Selection**: LangGraph can automatically choose the right Gmail tool based on user intent
- **Error Handling**: Built-in error handling and retry mechanisms for tool execution

```python
# Arcade AI tools automatically integrated
tools = manager.to_langchain(use_interrupts=True)
tool_node = ToolNode(tools)

# LangGraph automatically routes to appropriate tools
def should_continue(state: MessagesState):
    if state["messages"][-1].tool_calls:
        for tool_call in state["messages"][-1].tool_calls:
            if manager.requires_auth(tool_call["name"]):
                return "authorization"
        return "tools"
    return END
```

### 3. **Conversation Memory and State Persistence**

**Objective:** Maintain conversation context across sessions and provide personalized email assistance.

**Why LangGraph:**
- **Checkpointing**: Automatic state persistence using PostgreSQL or in-memory storage
- **Conversation History**: Maintains full conversation context for better AI responses
- **Session Management**: Handles user sessions and thread management

```python
# State persistence with checkpoints
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)

# Conversation context maintained
config = {
    "configurable": {
        "thread_id": thread_id,
        "user_id": user_id
    }
}
```

### 4. **Authorization and Security Management**

**Objective:** Handle Gmail API authorization seamlessly within the AI workflow.

**Why LangGraph + Arcade:**
- **Interrupt Handling**: LangGraph can pause execution for user authorization
- **OAuth Integration**: Arcade AI handles OAuth 2.0 flow for Gmail access
- **Secure Tool Execution**: Tools are executed with proper authentication

```python
def authorize(state: MessagesState, config: RunnableConfig):
    """Handle authorization interrupts."""
    user_id = config["configurable"].get("user_id")
    
    for tool_call in state["messages"][-1].tool_calls:
        tool_name = tool_call["name"]
        if manager.requires_auth(tool_name):
            auth_response = manager.authorize(tool_name, user_id)
            if auth_response.status != "completed":
                # LangGraph handles the interrupt
                return {"messages": [AIMessage(content=f"Authorization required for {tool_name}")]}
```

## 🏗️ Architectural Benefits

### 1. **Modular Design**

**Objective:** Create a maintainable, extensible system that can easily add new capabilities.

**Benefits:**
- **Separation of Concerns**: Each node handles a specific responsibility
- **Easy Extension**: New tools and capabilities can be added without changing core logic
- **Testability**: Individual components can be tested in isolation

```python
# Modular node design
workflow.add_node("agent", call_agent)           # AI reasoning
workflow.add_node("tools", tool_node)            # Tool execution
workflow.add_node("authorization", authorize)    # Auth handling
workflow.add_node("memory", memory_node)         # Memory management
```

### 2. **Scalable Architecture**

**Objective:** Build a system that can handle multiple users and complex workflows.

**Benefits:**
- **Concurrent Users**: LangGraph handles multiple user sessions
- **Resource Management**: Efficient resource allocation and cleanup
- **Performance**: Optimized execution with minimal latency

### 3. **Error Handling and Recovery**

**Objective:** Provide robust error handling and recovery mechanisms.

**Benefits:**
- **Graceful Degradation**: System continues to work even if some components fail
- **User Feedback**: Clear error messages and recovery suggestions
- **Debugging**: Comprehensive logging and error tracking

```python
try:
    for chunk in graph.stream(inputs, config=config, stream_mode="values"):
        # Process chunks
        pass
except Exception as e:
    error_msg = f"Error processing request: {str(e)}"
    writer(error_msg)
```

## 🎯 Specific Use Cases

### 1. **Intelligent Email Search**

**Objective:** Provide natural language email search with AI-powered understanding.

**Implementation:**
```python
# User: "Show me emails from LinkedIn about job opportunities"
# LangGraph workflow:
# 1. Agent analyzes user intent
# 2. Routes to Gmail_ListEmailsByHeader tool
# 3. Executes search with "linkedin.com" and "job" criteria
# 4. Formats and returns results
```

### 2. **Email Drafting and Composition**

**Objective:** Enable AI-assisted email drafting with context awareness.

**Implementation:**
```python
# User: "Draft a reply to the latest email"
# LangGraph workflow:
# 1. Agent identifies the need to draft a reply
# 2. Routes to Gmail_GetEmail to get the latest email
# 3. Routes to Gmail_WriteDraftEmail to create draft
# 4. Returns draft summary to user
```

### 3. **Email Analysis and Insights**

**Objective:** Provide intelligent analysis of email patterns and content.

**Implementation:**
```python
# User: "Summarize my emails from this week"
# LangGraph workflow:
# 1. Agent determines time range and scope
# 2. Routes to Gmail_ListEmails with date filters
# 3. Processes email content for summarization
# 4. Returns structured summary
```

## 🔄 Workflow Orchestration

### 1. **Conditional Routing**

**Objective:** Route requests to appropriate tools and agents based on user intent.

```python
def should_continue(state: MessagesState):
    last_message = state["messages"][-1]
    
    if last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            if manager.requires_auth(tool_call["name"]):
                return "authorization"  # Route to auth
        return "tools"  # Route to tool execution
    return END  # End workflow
```

### 2. **State Management**

**Objective:** Maintain conversation state and context across multiple interactions.

```python
# State includes conversation history, user preferences, and session data
class MessagesState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    thread_id: str
    user_id: str
```

### 3. **Tool Execution**

**Objective:** Execute Gmail tools with proper error handling and user feedback.

```python
# Tool execution with automatic retry and error handling
tool_node = ToolNode(tools)

# Tools are executed based on AI agent decisions
# Results are formatted and returned to user
```

## 🎯 Key Advantages

### 1. **Developer Experience**
- **Declarative Workflows**: Define workflows using simple Python functions
- **Built-in Debugging**: Comprehensive logging and error tracking
- **Hot Reloading**: Changes to workflow are reflected immediately

### 2. **User Experience**
- **Natural Language Interface**: Users can interact using natural language
- **Context Awareness**: System remembers previous interactions
- **Seamless Authorization**: OAuth flow is handled automatically

### 3. **Production Readiness**
- **Scalability**: Handles multiple users and complex workflows
- **Reliability**: Robust error handling and recovery mechanisms
- **Monitoring**: Built-in logging and performance tracking

## 🚀 Future Extensibility

### 1. **Additional Tools**
- **Calendar Integration**: Schedule meetings and events
- **Document Processing**: Analyze email attachments
- **Analytics**: Email usage patterns and insights

### 2. **Advanced Features**
- **Multi-Modal Support**: Voice and image input
- **Personalization**: User-specific preferences and behaviors
- **Integration**: Connect with other productivity tools

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎉 Conclusion

This AI-powered email assistant demonstrates the power of modern AI technologies working together. By combining Streamlit's user-friendly interface, LangGraph's workflow orchestration, and Arcade AI's Gmail integration, we've created a sophisticated application that can:

- **Process natural language queries** about emails
- **Maintain conversation context** across sessions
- **Provide professional email formatting** and display
- **Handle authentication and authorization** seamlessly
- **Prevent duplicate content** and ensure clean UI

The application showcases best practices in:
- **AI/ML integration** with modern frameworks
- **User experience design** with clean, professional interfaces
- **Data processing** with efficient content management
- **Security** with proper authentication and authorization
- **Scalability** with modular architecture and state management

This implementation serves as a solid foundation for building more sophisticated AI-powered applications that can interact with various APIs and provide intelligent assistance to users.

---

**Happy coding! 🚀**