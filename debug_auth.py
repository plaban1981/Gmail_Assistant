from langchain_arcade import ToolManager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
arcade_api_key = os.environ.get('ARCADE_API_KEY')

print('🔍 Debug: Checking Arcade authorization process...')
print(f'🔑 API Key: {arcade_api_key[:20]}...' if arcade_api_key else '❌ No API key')

# Initialize the tool manager
manager = ToolManager(api_key=arcade_api_key)
manager.init_tools(toolkits=['Gmail'])

try:
    # Get all available tools
    tools = manager.get_tools()
    print(f'📧 Available Gmail tools: {len([t for t in tools if "Gmail" in t.name])}')
    
    # Try to get authorization status
    user_id = 'nayakpplaban@gmailcom'
    print(f'👤 Checking authorization for: {user_id}')
    
    # Check if user is already authorized
    try:
        # Try to use a tool to see what happens
        gmail_tools = [t for t in tools if 'Gmail_ListEmails' in t.name]
        if gmail_tools:
            tool = gmail_tools[0]
            print(f'🔧 Testing tool: {tool.name}')
            
            # Try to call the tool to trigger authorization
            result = tool.invoke({'n_emails': 1}, config={'user_id': user_id})
            print(f'✅ Tool call successful: {result}')
            
    except Exception as e:
        error_msg = str(e)
        print(f'🔧 Tool call error: {error_msg}')
        
        # Look for authorization URL in error message
        if 'authorize' in error_msg.lower() or 'oauth' in error_msg.lower():
            print('🔗 Authorization required!')
            
            # Try the authorize method again with more details
            try:
                auth_response = manager.authorize('Gmail_ListEmails', user_id)
                print(f'📋 Full auth response: {auth_response}')
                print(f'📋 Auth response type: {type(auth_response)}')
                print(f'📋 Auth response attributes: {dir(auth_response)}')
                
                # Check all attributes for URL
                for attr in dir(auth_response):
                    if not attr.startswith('_'):
                        value = getattr(auth_response, attr)
                        print(f'  {attr}: {value}')
                        if 'http' in str(value):
                            print(f'🔗 FOUND URL: {value}')
                            
            except Exception as auth_error:
                print(f'❌ Authorization error: {auth_error}')

except Exception as e:
    print(f'❌ General error: {e}')

print('\n🔍 Debug completed.')
