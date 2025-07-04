import json
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_test_result():
    """Update the test_result.md file with WebSocket testing results"""
    try:
        # Read the current test_result.md file
        with open('/app/test_result.md', 'r') as f:
            content = f.read()
        
        # Find the WebSocket Real-time Communication section
        websocket_pattern = r'(  - task: "WebSocket Real-time Communication".*?status_history:.*?comment: "WebSocket connections are working properly\. Successfully established connections for multiple users, and the connection manager correctly tracks user online status\.")(.*?)(\n\n  - task:)'
        
        # Use re.DOTALL to match across multiple lines
        match = re.search(websocket_pattern, content, re.DOTALL)
        
        if match:
            # Add the new status history entry
            new_entry = """
      - working: true
        agent: "testing"
        comment: "Comprehensive testing of the real-time chat system confirms all WebSocket functionality is working correctly. Successfully tested WebSocket connections for multiple users, real-time message broadcasting to both direct and group chats, and file sharing through WebSockets. The ConnectionManager class properly handles user connections, disconnections, and message broadcasting. All tests passed with no issues."""
            
            # Replace the matched content with the updated content
            updated_content = content.replace(match.group(1) + match.group(2), match.group(1) + new_entry + match.group(2))
            
            # Write the updated content back to the file
            with open('/app/test_result.md', 'w') as f:
                f.write(updated_content)
            
            logger.info("Successfully updated WebSocket Real-time Communication status in test_result.md")
            return True
        else:
            logger.error("Could not find WebSocket Real-time Communication section in test_result.md")
            return False
    
    except Exception as e:
        logger.error(f"Error updating test_result.md: {e}")
        return False

if __name__ == "__main__":
    update_test_result()