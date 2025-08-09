#!/usr/bin/env python3
"""
Gmail CLI Assistant - A command-line interface for Gmail email management using Arcade AI and LangGraph.

This script provides the same functionality as the Streamlit app but through a command-line interface.
Users can search emails, create drafts, manage drafts, and more using natural language commands.

Usage:
    python gmail_cli_assistant.py
"""

import asyncio
import os
import sys
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import required libraries
try:
    from langchain_arcade import ToolManager
    from langchain_openai import ChatOpenAI
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.graph import END, START, MessagesState, StateGraph
    from langgraph.prebuilt import ToolNode
    from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
    from langchain_core.runnables import RunnableConfig
except ImportError as e:
    print(f"❌ Error: Missing required dependencies. Please install them with:")
    print(f"pip install langchain-arcade langchain-openai langgraph python-dotenv")
    sys.exit(1)

class GmailCLIAssistant:
    """Command-line interface for Gmail email management using Arcade AI and LangGraph."""
    
    def __init__(self):
        """Initialize the Gmail CLI Assistant."""
        self.arcade_api_key = os.environ.get("ARCADE_API_KEY")
        self.openai_api_key = os.environ.get("OPENAIAPIKEY")
        self.model_choice = os.environ.get("MODEL_CHOICE", "gpt-4o-mini")
        self.user_email = os.environ.get("EMAIL", "nayakpplaban@gmail.com")  # Default to nayakpplaban@gmail.com
        
        if not self.arcade_api_key:
            print("❌ Error: ARCADE_API_KEY not found in environment variables")
            sys.exit(1)
        
        if not self.openai_api_key:
            print("❌ Error: OPENAIAPIKEY not found in environment variables")
            sys.exit(1)
        
        # No need to exit if EMAIL not found since we have a default
        if not os.environ.get("EMAIL"):
            print(f"ℹ️  EMAIL not found in environment variables, using default: {self.user_email}")
        
        self.manager = None
        self.tools = []
        self.tool_node = None
        self.model_with_tools = None
        self.graph = None
        self.thread_id = None
        
        print("🔧 Initializing Gmail CLI Assistant...")
        self._initialize_tools()
        self._build_graph()
        print("✅ Gmail CLI Assistant initialized successfully!")
    
    def _initialize_tools(self):
        """Initialize Arcade AI tools."""
        try:
            print("🔧 Initializing Arcade AI tools...")
            self.manager = ToolManager(api_key=self.arcade_api_key)
            self.manager.init_tools(toolkits=["Gmail"])
            self.tools = self.manager.to_langchain(use_interrupts=True)
            self.tool_node = ToolNode(self.tools)
            
            print(f"✅ Loaded {len(self.tools)} Gmail tools:")
            for i, tool in enumerate(self.tools, 1):
                tool_name = getattr(tool, 'name', f'Tool_{i}')
                print(f"  {i:2d}. {tool_name}")
            
        except Exception as e:
            print(f"❌ Error initializing tools: {e}")
            sys.exit(1)
    
    def _build_graph(self):
        """Build the LangGraph workflow."""
        try:
            print("🔧 Building LangGraph workflow...")
            
            # Create the model
            model = ChatOpenAI(model=self.model_choice, api_key=self.openai_api_key, temperature=0)
            self.model_with_tools = model.bind_tools(self.tools)
            
            # Build the graph
            workflow = StateGraph(MessagesState)
            
            # Add nodes
            workflow.add_node("agent", self._call_agent)
            workflow.add_node("tools", self.tool_node)
            workflow.add_node("authorization", self._authorize)
            
            # Add edges
            workflow.add_edge(START, "agent")
            workflow.add_conditional_edges("agent", self._should_continue, {
                "authorization": "authorization",
                "tools": "tools",
                END: END
            })
            workflow.add_edge("authorization", "tools")
            workflow.add_edge("tools", "agent")  # Add edge back to agent after tools
            
            self.graph = workflow.compile()
            print("✅ LangGraph workflow built successfully!")
            
        except Exception as e:
            print(f"❌ Error building graph: {e}")
            sys.exit(1)
    
    def _call_agent(self, state: MessagesState):
        """Call the AI agent with the current state."""
        messages = state["messages"]
        
        # Add system message
        system_message = """You are a helpful AI assistant with access to Gmail tools. When users ask about emails, you MUST use the Gmail tools to retrieve actual email data.

CRITICAL: Do not just repeat the user's query - you must use the Gmail tools to actually retrieve emails.

Available Gmail tools:
- Gmail_ListEmails: List emails from inbox with search criteria
- Gmail_ListEmailsByHeader: List emails by specific header criteria
- Gmail_GetEmail: Get specific email by ID
- Gmail_SearchEmails: Search emails with advanced criteria
- Gmail_WriteDraftEmail: Create a draft email (saves to Gmail drafts folder)
- Gmail_ListDraftEmails: List all draft emails in the user's drafts folder
- Gmail_DeleteDraftEmail: Delete a specific draft email
- Gmail_SendDraftEmail: Send a draft email
- Gmail_UpdateDraftEmail: Update an existing draft email
- Gmail_WriteDraftReplyEmail: Create a draft reply to an existing email
- Gmail_ReplyToEmail: Reply to an email directly
- Gmail_SendEmail: Send an email directly
- Gmail_GetThread: Get a specific email thread
- Gmail_ListThreads: List email threads
- Gmail_SearchThreads: Search for email threads
- Gmail_ListLabels: List Gmail labels
- Gmail_CreateLabel: Create a new Gmail label
- Gmail_ChangeEmailLabels: Change labels for emails
- Gmail_TrashEmail: Move email to trash

CRITICAL FOR DRAFT EMAILS:
- ALWAYS provide a meaningful body content when creating draft emails
- If the user doesn't specify body content, create a professional default body
- NEVER create draft emails with empty body content
- Use professional templates when body content is missing

Example tool usage:
- For "show me top 5 emails from today": Use Gmail_ListEmails with {"query": "after:today", "max_results": 5}
- For "find emails about meetings": Use Gmail_ListEmails with {"query": "subject:meeting OR body:meeting"}
- For "emails from specific sender": Use Gmail_ListEmails with {"query": "from:john@example.com"}
- For "emails with specific subject": Use Gmail_ListEmails with {"query": "subject:meeting"} or Gmail_ListEmailsByHeader with {"header": "subject", "value": "meeting"}
- For "emails related to specific subject": Use Gmail_ListEmails with {"query": "subject:RE: [#8468] Re: Exciting New Courses"} or {"query": "subject:Exciting New Courses"}
- For "draft a reply": Use Gmail_WriteDraftReplyEmail with appropriate subject, body, and recipient
- For "create a new draft": Use Gmail_WriteDraftEmail with appropriate subject, body, and recipient
- For "show me my drafts": Use Gmail_ListDraftEmails to list all draft emails

IMPORTANT: Always use the tools to retrieve actual email data and provide informative responses about what you find. If no emails are found, provide a helpful message indicating that no emails matched the search criteria. After using tools, always provide a summary of what you found or accomplished."""
        
        messages_with_system = [SystemMessage(content=system_message)] + messages
        response = self.model_with_tools.invoke(messages_with_system)
        
        return {"messages": [response]}
    
    def _should_continue(self, state: MessagesState):
        """Determine the next step in the workflow."""
        last_message = state["messages"][-1]
        
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            print(f"🔧 Found {len(last_message.tool_calls)} tool calls")
            for tool_call in last_message.tool_calls:
                tool_name = tool_call.get("name", "Unknown")
                print(f"🔧 Tool call: {tool_name}")
                if self.manager.requires_auth(tool_name):
                    print(f"🔧 Tool {tool_name} requires authorization")
                    return "authorization"
            print(f"🔧 No authorization required, proceeding to tools")
            return "tools"
        return END
    
    def _check_authorization_methods(self):
        """Check if the required authorization methods exist."""
        has_wait_for_auth = hasattr(self.manager, 'wait_for_auth')
        has_is_authorized = hasattr(self.manager, 'is_authorized')
        return has_wait_for_auth, has_is_authorized

    def _authorize(self, state: MessagesState, config: RunnableConfig):
        """Handle Gmail authorization."""
        user_id = config["configurable"].get("user_id", self.user_email.replace(".", ""))
        
        for tool_call in state["messages"][-1].tool_calls:
            tool_name = tool_call["name"]
            if self.manager.requires_auth(tool_name):
                print(f"🔐 Authorization required for {tool_name}...")
                
                try:
                    # Get authorization URL
                    auth_response = self.manager.authorize(tool_name, user_id)
                    
                    if hasattr(auth_response, 'status') and auth_response.status == "pending":
                        # Authorization is pending - user needs to complete it
                        if hasattr(auth_response, 'url') and auth_response.url:
                            print(f"\n🌐 **Authorization Required**")
                            print(f"   The agent needs access to your **{tool_name}** to complete your request.")
                            print(f"   Please visit the following URL to authorize:")
                            print(f"   🔗 {auth_response.url}")
                            print(f"   After completing authorization, press Enter to continue...")
                            
                            # Wait for user to complete authorization
                            input("   Press Enter when you've completed authorization...")
                            
                            # Check if we have the required authorization methods
                            has_wait_for_auth, has_is_authorized = self._check_authorization_methods()
                            
                            if has_wait_for_auth and has_is_authorized and hasattr(auth_response, 'id'):
                                print(f"   ⏳ Waiting for authorization to complete...")
                                self.manager.wait_for_auth(auth_response.id)
                                
                                # Check if authorization is now complete
                                if self.manager.is_authorized(auth_response.id):
                                    print(f"   ✅ Authorization completed for {tool_name}")
                                else:
                                    print(f"   ⚠️ Authorization still pending for {tool_name}")
                                    return {"messages": [AIMessage(content=f"Authorization required for {tool_name}. Please complete the authorization process and try again.")]}
                            else:
                                # Fallback: check authorization status again
                                print(f"   ⏳ Checking authorization status...")
                                check_response = self.manager.authorize(tool_name, user_id)
                                if hasattr(check_response, 'status') and check_response.status == "completed":
                                    print(f"   ✅ Authorization completed for {tool_name}")
                                else:
                                    print(f"   ⚠️ Authorization still pending for {tool_name}")
                                    return {"messages": [AIMessage(content=f"Authorization required for {tool_name}. Please complete the authorization process and try again.")]}
                        else:
                            print(f"⚠️ Authorization URL not available for {tool_name}")
                            return {"messages": [AIMessage(content=f"Authorization required for {tool_name} but no authorization URL was provided.")]}
                    elif hasattr(auth_response, 'status') and auth_response.status == "completed":
                        print(f"✅ Authorization completed for {tool_name}")
                    else:
                        print(f"⚠️ Authorization not completed for {tool_name}")
                        return {"messages": [AIMessage(content=f"Authorization required for {tool_name}. Please try again.")]}
                        
                except Exception as e:
                    print(f"❌ Error during authorization for {tool_name}: {e}")
                    return {"messages": [AIMessage(content=f"Authorization failed for {tool_name}: {str(e)}")]}
        
        return {"messages": []}
    
    async def process_command(self, user_input: str) -> str:
        """Process a user command and return the response."""
        try:
            # Generate thread ID if not exists
            if not self.thread_id:
                import uuid
                self.thread_id = str(uuid.uuid4())
            
            # Prepare config
            config = {
                "configurable": {
                    "thread_id": self.thread_id,
                    "user_id": self.user_email.replace(".", "")
                }
            }
            
            # Prepare inputs
            inputs = {"messages": [HumanMessage(content=user_input)]}
            
            print(f"🤖 Processing: {user_input[:50]}{'...' if len(user_input) > 50 else ''}")
            
            # Stream the response
            full_response = ""
            authorization_required = False
            tool_executed = False
            all_messages = []
            
            async for chunk in self.graph.astream(inputs, config=config):
                print(f"🔍 Processing chunk: {type(chunk)}")
                
                if isinstance(chunk, dict) and "messages" in chunk:
                    last_message = chunk["messages"][-1]
                    all_messages.append(last_message)
                    print(f"📝 Last message type: {type(last_message)}")
                    
                    # Check for content in the message
                    if hasattr(last_message, 'content') and last_message.content:
                        content = str(last_message.content)
                        print(f"📄 Content: {content[:100]}{'...' if len(content) > 100 else ''}")
                        
                        if content and content.strip() and content.lower() != 'null':
                            # Check if this is an authorization message
                            if "authorization required" in content.lower() or "authorization" in content.lower():
                                authorization_required = True
                            elif "tool" in content.lower() or "email" in content.lower() or "draft" in content.lower():
                                tool_executed = True
                            full_response += content + "\n"
                    
                    # Check for tool calls
                    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                        print(f"🔧 Tool calls found: {len(last_message.tool_calls)}")
                        for tool_call in last_message.tool_calls:
                            print(f"🔧 Tool call: {tool_call.get('name', 'Unknown')}")
                            tool_executed = True
                    
                    # Check for tool results - this is the key part that was missing
                    if hasattr(last_message, 'tool_results') and last_message.tool_results:
                        print(f"🔧 Tool results found: {len(last_message.tool_results)}")
                        for tool_result in last_message.tool_results:
                            print(f"🔧 Tool result: {tool_result.get('content', 'No content')[:100]}...")
                            tool_executed = True
                            if tool_result.get('content'):
                                full_response += str(tool_result['content']) + "\n"
                    
                    # Check for additional content in the message
                    if hasattr(last_message, 'additional_kwargs') and last_message.additional_kwargs:
                        print(f"🔧 Additional kwargs found: {last_message.additional_kwargs}")
                        if 'tool_results' in last_message.additional_kwargs:
                            tool_results = last_message.additional_kwargs['tool_results']
                            print(f"🔧 Tool results from kwargs: {len(tool_results)}")
                            for tool_result in tool_results:
                                if isinstance(tool_result, dict) and 'content' in tool_result:
                                    content = tool_result['content']
                                    print(f"🔧 Tool result content: {content[:100]}...")
                                    full_response += str(content) + "\n"
                                    tool_executed = True
                    
                    # Check for any other response format
                    if hasattr(last_message, '__dict__'):
                        for key, value in last_message.__dict__.items():
                            if key not in ['content', 'tool_calls', 'tool_results', 'additional_kwargs'] and value:
                                print(f"🔧 Additional field {key}: {str(value)[:100]}...")
                                if isinstance(value, str) and value.strip():
                                    full_response += str(value) + "\n"
                                    tool_executed = True
                    
                    # Check for tool execution results in the message
                    if hasattr(last_message, 'tool_results') and last_message.tool_results:
                        for tool_result in last_message.tool_results:
                            if isinstance(tool_result, dict):
                                if 'content' in tool_result and tool_result['content']:
                                    content = tool_result['content']
                                    print(f"🔧 Tool result content found: {content[:100]}...")
                                    full_response += str(content) + "\n"
                                    tool_executed = True
                                elif 'output' in tool_result and tool_result['output']:
                                    output = tool_result['output']
                                    print(f"🔧 Tool result output found: {output[:100]}...")
                                    full_response += str(output) + "\n"
                                    tool_executed = True
                    
                    # Check for tool execution results in the message - additional check
                    if hasattr(last_message, 'tool_results') and last_message.tool_results:
                        for tool_result in last_message.tool_results:
                            if isinstance(tool_result, dict):
                                # Check for any content in the tool result
                                for key, value in tool_result.items():
                                    if key in ['content', 'output', 'result', 'data'] and value:
                                        print(f"🔧 Tool result {key} found: {str(value)[:100]}...")
                                        full_response += str(value) + "\n"
                                        tool_executed = True
                                        break
            
            # If no response was received, try to extract from all messages
            if not full_response.strip() and all_messages:
                print(f"🔍 No direct response found, checking {len(all_messages)} messages for content...")
                
                # Check all messages in reverse order for content
                for message in reversed(all_messages):
                    print(f"🔍 Checking message type: {type(message)}")
                    
                    # Check for AIMessage content (final response)
                    if hasattr(message, 'content') and message.content:
                        content = str(message.content)
                        if content and content.strip() and content.lower() != 'null':
                            print(f"🔍 Found AIMessage content: {content[:100]}...")
                            full_response = content
                            break
                    
                    # Check for ToolMessage content (tool results)
                    if hasattr(message, 'tool_results') and message.tool_results:
                        for tool_result in message.tool_results:
                            if isinstance(tool_result, dict):
                                for key, value in tool_result.items():
                                    if key in ['content', 'output', 'result', 'data'] and value:
                                        print(f"🔍 Found ToolMessage content in {key}: {str(value)[:100]}...")
                                        full_response = str(value)
                                        break
                                if full_response:
                                    break
                        if full_response:
                            break
                    
                    # Check for additional kwargs
                    if hasattr(message, 'additional_kwargs') and message.additional_kwargs:
                        if 'tool_results' in message.additional_kwargs:
                            tool_results = message.additional_kwargs['tool_results']
                            for tool_result in tool_results:
                                if isinstance(tool_result, dict) and 'content' in tool_result:
                                    content = tool_result['content']
                                    if content:
                                        print(f"🔍 Found content in additional_kwargs: {content[:100]}...")
                                        full_response = str(content)
                                        break
                            if full_response:
                                break
            
            # If still no response, try to get the final state
            if not full_response.strip() and all_messages:
                print(f"🔍 Trying to get final state from {len(all_messages)} messages...")
                
                # Get the final message
                final_message = all_messages[-1]
                print(f"🔍 Final message type: {type(final_message)}")
                
                # Check if it's an AIMessage with content
                if hasattr(final_message, 'content') and final_message.content:
                    content = str(final_message.content)
                    if content and content.strip() and content.lower() != 'null':
                        print(f"🔍 Found final message content: {content[:100]}...")
                        full_response = content
                
                # If still no content, check for tool results in the final message
                elif hasattr(final_message, 'tool_results') and final_message.tool_results:
                    for tool_result in final_message.tool_results:
                        if isinstance(tool_result, dict):
                            for key, value in tool_result.items():
                                if key in ['content', 'output', 'result', 'data'] and value:
                                    print(f"🔍 Found final tool result in {key}: {str(value)[:100]}...")
                                    full_response = str(value)
                                    break
                            if full_response:
                                break
            
            # If still no response, try to get the final state from the graph
            if not full_response.strip():
                print(f"🔍 Trying to get final state from graph...")
                try:
                    # Get the final state from the graph
                    final_state = self.graph.get_state(config)
                    if hasattr(final_state, 'messages') and final_state.messages:
                        final_messages = final_state.messages
                        print(f"🔍 Found {len(final_messages)} messages in final state")
                        
                        # Check the last message in the final state
                        if final_messages:
                            last_final_message = final_messages[-1]
                            print(f"🔍 Last final message type: {type(last_final_message)}")
                            
                            if hasattr(last_final_message, 'content') and last_final_message.content:
                                content = str(last_final_message.content)
                                if content and content.strip() and content.lower() != 'null':
                                    print(f"🔍 Found final state content: {content[:100]}...")
                                    full_response = content
                            
                            elif hasattr(last_final_message, 'tool_results') and last_final_message.tool_results:
                                for tool_result in last_final_message.tool_results:
                                    if isinstance(tool_result, dict):
                                        for key, value in tool_result.items():
                                            if key in ['content', 'output', 'result', 'data'] and value:
                                                print(f"🔍 Found final state tool result in {key}: {str(value)[:100]}...")
                                                full_response = str(value)
                                                break
                                        if full_response:
                                            break
                except Exception as e:
                    print(f"🔍 Error getting final state: {e}")
            
            # If no response was received but tools were executed, try to get more information
            if not full_response.strip() and tool_executed:
                return """🔍 Tool executed but no response received.

This might be because:
1. The tool executed successfully but returned no data
2. The search criteria didn't match any emails
3. There was an issue with the tool response

**Try these alternatives:**
- "Show me emails from today" - to see recent emails
- "List my drafts" - to see your draft emails
- "Search for emails about [topic]" - to search with different criteria

**Or try rephrasing your request:**
- "Find emails with subject containing 'Exciting New Courses'"
- "Search for emails about AI Pioneer Program"
- "Show me emails from today about courses" """
            
            # If authorization was required but not completed, provide guidance
            if authorization_required and not full_response.strip():
                return """🔐 Authorization Required

It looks like you need to authorize Gmail access for this operation. 

**To complete authorization:**
1. Look for the authorization URL above
2. Click on the URL or copy it to your browser
3. Complete the Gmail authorization process
4. Return to this CLI and press Enter when prompted

**If you don't see an authorization URL:**
- Try running the command again
- Make sure you're using the correct Gmail account
- Check that your API keys are properly configured

**Alternative approach:**
Try using a simpler search first, like:
- "Show me emails from today"
- "List my drafts"
- "Search for emails about [topic]"

Would you like to try again with a different command?"""
            
            return full_response.strip() if full_response.strip() else "⚠️ No response received from the tool execution."
            
        except Exception as e:
            print(f"❌ Error in process_command: {e}")
            return f"❌ Error processing command: {str(e)}\n\n💡 Try using a simpler command like 'Show me emails from today' or 'List my drafts'."
    
    def display_help(self):
        """Display help information."""
        help_text = """
🎯 Gmail CLI Assistant - Help

This assistant helps you manage your Gmail emails using natural language commands.

📧 Available Commands:

1. **Email Search:**
   - "Show me emails from today"
   - "Find emails from john@example.com"
   - "Search for emails about meetings"
   - "List top 5 emails from this week"

2. **Draft Management:**
   - "Create a new email to test@example.com with subject 'Test' and body 'Hello'"
   - "Draft a reply to the latest email"
   - "Show me my drafts"
   - "Delete draft with subject 'Test'"

3. **Email Operations:**
   - "Send the draft with subject 'Test'"
   - "Update draft with subject 'Test' with new body 'Updated content'"
   - "Get email with ID 12345"

4. **General:**
   - "help" - Show this help message
   - "quit" or "exit" - Exit the application
   - "clear" - Clear the screen

💡 Tips:
- Use natural language - "Show me emails from LinkedIn"
- Be specific - "Create a draft email to john@example.com about the meeting"
- Check drafts - "Show me my drafts" to see all saved drafts

🔧 Examples:
- "Show me emails from today"
- "Create a new email to test@example.com with subject 'Meeting Request' and body 'Hi, I would like to schedule a meeting.'"
- "Draft a reply to the latest email"
- "Show me my drafts"
"""
        print(help_text)
    
    def run(self):
        """Run the CLI assistant."""
        print("🚀 Gmail CLI Assistant")
        print("=" * 50)
        print(f"👤 User: {self.user_email}")
        print(f"🤖 Model: {self.model_choice}")
        print("=" * 50)
        print("Type 'help' for available commands or 'quit' to exit.")
        print()
        
        while True:
            try:
                # Get user input
                user_input = input("📧 Gmail Assistant > ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    self.display_help()
                    continue
                elif user_input.lower() == 'clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue
                
                # Process the command
                print("🔄 Processing...")
                response = asyncio.run(self.process_command(user_input))
                
                if response:
                    print("\n" + "=" * 50)
                    print("🤖 Response:")
                    print("=" * 50)
                    print(response)
                    print("=" * 50)
                else:
                    print("⚠️ No response received.")
                
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                print("Please try again or type 'help' for assistance.")

def main():
    """Main function to run the Gmail CLI Assistant."""
    try:
        assistant = GmailCLIAssistant()
        assistant.run()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 