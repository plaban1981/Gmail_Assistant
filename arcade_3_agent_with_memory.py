from langchain_arcade import ToolManager
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from dotenv import load_dotenv
import sys
import os
import uuid

# Load in the environment variables
load_dotenv()
arcade_api_key = os.environ.get("ARCADE_API_KEY")
openai_api_key = os.environ.get("OPENAIAPIKEY")
model_choice = os.environ.get("MODEL_CHOICE")
email = os.environ.get("EMAIL")
database_url = os.environ.get("DATABASE_URL")

# Add debug print for API key
print(f"🔧 Agent: OpenAI API key loaded: {openai_api_key[:20]}..." if openai_api_key else "❌ Agent: No OpenAI API key found")

# Initialize the tool manager and fetch tools compatible with langgraph
manager = ToolManager(api_key=arcade_api_key)
print(f"🔧 Agent: ToolManager initialized with Arcade API key: {arcade_api_key[:20]}..." if arcade_api_key else "❌ Agent: No Arcade API key")

manager.init_tools(toolkits=["Gmail"])
tools = manager.to_langchain(use_interrupts=True)
print(f"🔧 Agent: Converted {len(tools)} tools to LangChain format")

# Print available tools with more details
print("🔧 Agent: Available tools:")
for i, tool in enumerate(tools):
    tool_name = tool.name if hasattr(tool, 'name') else str(tool)
    requires_auth = manager.requires_auth(tool_name) if hasattr(manager, 'requires_auth') else 'Unknown'
    print(f"  🔧 Tool {i+1}: {tool_name} - Requires auth: {requires_auth}")
    if hasattr(tool, 'description'):
        print(f"    Description: {tool.description[:100]}...")
    if hasattr(tool, 'args_schema'):
        print(f"    Args schema: {tool.args_schema}")
    if hasattr(tool, 'name'):
        print(f"    Tool name: {tool.name}")
    if hasattr(tool, 'function'):
        print(f"    Function: {tool.function.name if hasattr(tool.function, 'name') else 'Unknown'}")

# Initialize the prebuilt tool node
tool_node = ToolNode(tools)
print("✅ Agent: ToolNode initialized successfully")

# Create a language model instance and bind it with the tools
print(f"🔧 Agent: Creating ChatOpenAI with model: {model_choice}")
print(f"🔧 Agent: Using API key: {openai_api_key[:20]}..." if openai_api_key else "❌ Agent: No API key provided")
model = ChatOpenAI(model=model_choice, api_key=openai_api_key, temperature=0)
model_with_tools = model.bind_tools(tools)
print("✅ Agent: ChatOpenAI model created successfully")
print(f"🔧 Agent: Model bound with {len(tools)} tools")

# Print tool names for debugging
print("🔧 Agent: Tool names available to model:")
for tool in tools:
    if hasattr(tool, 'name'):
        print(f"  - {tool.name}")
    else:
        print(f"  - {str(tool)}")

# Print tool descriptions for debugging
print("🔧 Agent: Tool descriptions:")
for tool in tools:
    if hasattr(tool, 'description'):
        print(f"  - {tool.name}: {tool.description[:100]}...")
    else:
        print(f"  - {tool.name}: No description available")


# Function to invoke the model and get a response
def call_agent(state: MessagesState):
    messages = state["messages"]
    
    # Add system message to guide the model on how to use Gmail tools
    system_message = """You are a helpful AI assistant with access to Gmail tools. When users ask about emails, you MUST use the Gmail tools to retrieve actual email data.

CRITICAL: Do not just repeat the user's query - you must use the Gmail tools to actually retrieve emails.

For email queries like "show me top 5 emails from today":
1. Use Gmail_ListEmails tool with appropriate search criteria
2. For "top 5 emails from today" use: {"query": "after:today", "max_results": 5}
3. For "emails from today" use: {"query": "after:today"}
4. For "emails from specific sender" use: {"query": "from:example@gmail.com"}

For email drafting like "draft a reply":
1. Use Gmail_WriteDraftEmail tool to create a draft email
2. Use Gmail_WriteDraftReplyEmail tool to create a draft reply to an existing email
3. Provide a helpful response explaining what you've done
4. Include details about the draft email (subject, recipient, etc.)

Available Gmail tools:
- Gmail_ListEmails: List emails from inbox with search criteria
- Gmail_GetEmail: Get specific email by ID
- Gmail_SearchEmails: Search emails with advanced criteria
- Gmail_WriteDraftEmail: Create a draft email (saves to Gmail drafts folder)
- Gmail_ListDraftEmails: List all draft emails in the user's drafts folder
- Gmail_DeleteDraftEmail: Delete a specific draft email
- Gmail_SendDraftEmail: Send a draft email
- Gmail_UpdateDraftEmail: Update an existing draft email
- Gmail_WriteDraftReplyEmail: Create a draft reply to an existing email

Example tool usage:
- For "top 5 emails from today": Use Gmail_ListEmails with {"query": "after:today", "max_results": 5}
- For "emails from yesterday": Use Gmail_ListEmails with {"query": "after:yesterday before:today"}
- For "unread emails": Use Gmail_ListEmails with {"query": "is:unread"}
- For "draft a reply": Use Gmail_WriteDraftReplyEmail with appropriate subject, body, and recipient
- For "create a new draft": Use Gmail_WriteDraftEmail with appropriate subject, body, and recipient
- For "show me my drafts": Use Gmail_ListDraftEmails to list all draft emails
- For "delete a draft": Use Gmail_DeleteDraftEmail with the draft ID
- For "send a draft": Use Gmail_SendDraftEmail with the draft ID
- For "update a draft": Use Gmail_UpdateDraftEmail with the draft ID and new content

When using Gmail_ListEmails, you can pass these arguments:
- query: Search query (e.g., "after:today", "from:example@gmail.com", "subject:meeting")
- max_results: Maximum number of results to return (default is 10)

When using Gmail_WriteDraftEmail, you can pass these arguments:
- subject: Email subject line (REQUIRED)
- body: Email body content (REQUIRED - must not be empty)
- recipient: Email recipient address (REQUIRED)

CRITICAL FOR DRAFT EMAILS:
- ALWAYS provide a meaningful body content when creating draft emails
- If the user doesn't specify body content, create a professional default body
- For empty body requests, use a professional template like:
  "Dear [Recipient],
  
  [Your message here]
  
  Best regards,
  [Your name]"
- NEVER create draft emails with empty body content
- If the user only provides a subject, create a professional body based on the subject

When using Gmail_WriteDraftReplyEmail, you can pass these arguments:
- subject: Email subject line (usually starts with "Re:")
- body: Email body content (REQUIRED - must not be empty)
- recipient: Email recipient address
- thread_id: ID of the email thread to reply to (if available)

IMPORTANT: Always use the tools to retrieve actual email data and provide informative responses about what you find. Do not just repeat the user's query. After using tools, provide a helpful summary of what you accomplished.

For draft emails specifically:
- Draft emails created with Gmail_WriteDraftEmail are automatically saved to the user's Gmail drafts folder
- Draft replies created with Gmail_WriteDraftReplyEmail are automatically saved to the user's Gmail drafts folder
- Users can access their drafts at: https://mail.google.com/mail/u/0/#drafts
- Draft emails will appear in the Gmail web interface under the "Drafts" folder
- Users can edit, send, or delete drafts directly from Gmail
- ALWAYS provide meaningful body content for draft emails

Tool Selection Guidelines:
- Use Gmail_WriteDraftReplyEmail when the user wants to reply to an existing email
- Use Gmail_WriteDraftEmail when the user wants to create a new email from scratch
- Use Gmail_ListDraftEmails when the user wants to see all their saved drafts
- Use Gmail_DeleteDraftEmail when the user wants to delete a specific draft
- Use Gmail_SendDraftEmail when the user wants to send an existing draft
- Use Gmail_UpdateDraftEmail when the user wants to modify an existing draft

DRAFT EMAIL BODY REQUIREMENTS:
- NEVER create draft emails with empty body content
- Always provide professional, meaningful content
- If user doesn't specify body, create a professional template
- Use appropriate greetings and closings
- Make the content relevant to the subject and recipient"""
    
    # Add system message if not already present
    messages_with_system = messages[:]
    if not messages or not isinstance(messages[0], SystemMessage):
        messages_with_system = [SystemMessage(content=system_message)] + messages
    
    print(f"🔧 Agent: Processing {len(messages_with_system)} messages")
    print(f"🔧 Agent: Last message content: {messages_with_system[-1].content[:100]}...")
    
    # Use invoke for synchronous processing
    response = model_with_tools.invoke(messages_with_system)
    
    print(f"🔧 Agent: Response generated with {len(response.tool_calls) if hasattr(response, 'tool_calls') and response.tool_calls else 0} tool calls")
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for i, tool_call in enumerate(response.tool_calls):
            print(f"🔧 Agent: Tool call {i+1}: {tool_call.get('name', 'Unknown')} with args: {tool_call.get('args', {})}")
    else:
        print(f"🔧 Agent: No tool calls generated - response content: {response.content}...")
        print(f"🔧 Agent: This might indicate the model is not using tools properly")
    
    # Return the updated message history
    return {"messages": [response]}


# Function to determine the next step in the workflow based on the last message
def should_continue(state: MessagesState):
    last_message = state["messages"][-1]
    print(f"🔧 Agent: should_continue called with message type: {type(last_message)}")
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        print(f"🔧 Agent: Found {len(last_message.tool_calls)} tool calls")
        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get("name", "Unknown")
            print(f"🔧 Agent: Tool call: {tool_name}")
            if manager.requires_auth(tool_name):
                print(f"🔧 Agent: Tool {tool_name} requires authorization")
                return "authorization"
        print(f"🔧 Agent: No authorization required, proceeding to tools")
        return "tools"  # Proceed to tool execution if no authorization is needed
    else:
        print(f"🔧 Agent: No tool calls found, ending workflow")
        return END  # End the workflow if no tool calls are present


# Function to handle authorization for tools that require it
def authorize(state: MessagesState, *args, **kwargs):
    # Extract config from args or kwargs
    config = None
    if args and hasattr(args[0], 'get'):
        config = args[0]
    elif 'config' in kwargs:
        config = kwargs['config']
    
    # Handle the case where config might not be passed
    if config is None:
        # Try to get user_id from the state or use a default
        user_id = "default_user"
    else:
        user_id = config["configurable"].get("user_id", "default_user")
    
    for tool_call in state["messages"][-1].tool_calls:
        tool_name = tool_call["name"]
        if not manager.requires_auth(tool_name):
            continue
        auth_response = manager.authorize(tool_name, user_id)
        if auth_response.status != "completed":
            # Prompt the user to visit the authorization URL
            print(f"Visit the following URL to authorize: {auth_response.url}")

            # Wait for the user to complete the authorization
            # and then check the authorization status again
            manager.wait_for_auth(auth_response.id)
            if not manager.is_authorized(auth_response.id):
                # This stops execution if authorization fails
                raise ValueError("Authorization failed")

    return {"messages": []}


# Builds the LangGraph workflow with memory
def build_graph():
    # Build the workflow graph using StateGraph
    workflow = StateGraph(MessagesState)

    # Add nodes (steps) to the graph
    workflow.add_node("agent", call_agent)
    workflow.add_node("tools", tool_node)
    workflow.add_node("authorization", authorize)

    # Define the edges and control flow between nodes
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue, ["authorization", "tools", END])
    workflow.add_edge("authorization", "tools")
    workflow.add_edge("tools", "agent")

    # Set up memory for checkpointing the state
    memory = MemorySaver()

    # Compile the graph with the checkpointer
    graph = workflow.compile(checkpointer=memory)
    return graph


workflow = build_graph()


async def main():
    async with (
        # AsyncPostgresStore.from_conn_string(database_url) as store, # This line was removed as per the new_code
        # AsyncPostgresSaver.from_conn_string(database_url) as checkpointer, # This line was removed as per the new_code
    ):
        # Run these lines the first time to set up everything in Postgres
        # await checkpointer.setup()
        # await store.setup()

        graph = build_graph()
        
        # User query
        user_query = "What emails do I have in my inbox from today? Remember my question too"
        
        # Build messages list with user query
        messages = [
            HumanMessage(content=user_query)
        ]
        
        # Define the input with messages
        inputs = {
            "messages": messages
        }

        # Configuration with thread and user IDs for authorization purposes
        config = {"configurable": {"thread_id": "4", "user_id": email}}

        # Run the graph and stream the outputs
        async for chunk in graph.astream(inputs, config=config, stream_mode="values"):
            # Pretty-print the last message in the chunk
            chunk["messages"][-1].pretty_print()
        

if __name__ == "__main__":
    import asyncio

    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())