from langchain_arcade import ToolManager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
arcade_api_key = os.environ.get('ARCADE_API_KEY')

# Initialize the tool manager
manager = ToolManager(api_key=arcade_api_key)
manager.init_tools(toolkits=['Gmail'])

print('🔍 Getting fresh Gmail authorization URL...')

try:
    # Get authorization for your specific user ID (from logs)
    user_id = 'nayakpplaban@gmailcom'
    print(f'👤 User ID: {user_id}')
    
    # Try different Gmail tools to get auth URL
    tools_to_try = ['Gmail_WriteDraftEmail', 'Gmail_ListEmails', 'Gmail_WriteDraftReplyEmail']
    
    for tool_name in tools_to_try:
        try:
            print(f'🔧 Trying to authorize: {tool_name}')
            auth_response = manager.authorize(tool_name, user_id)
            
            if hasattr(auth_response, 'url') and auth_response.url:
                print(f'✅ SUCCESS! Authorization URL found:')
                print(f'🔗 {auth_response.url}')
                print(f'📊 Status: {auth_response.status}')
                print(f'🆔 Auth ID: {auth_response.id}')
                print(f'📋 Scopes: {auth_response.scopes}')
                
                print(f'\n🎯 NEXT STEPS:')
                print(f'1. Copy the URL above')
                print(f'2. Open it in your browser')
                print(f'3. Sign in with nayakpplaban@gmail.com')
                print(f'4. Grant Gmail permissions')
                print(f'5. After authorization, try creating drafts again in Streamlit')
                break
            else:
                print(f'❌ No URL in response for {tool_name}')
                
        except Exception as e:
            print(f'❌ Error with {tool_name}: {e}')
            continue
    
except Exception as e:
    print(f'❌ General error: {e}')

print('\n🏁 Authorization script completed.')
