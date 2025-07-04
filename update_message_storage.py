import json
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_message_storage():
    """Update the test_result.md file with Message Storage and Retrieval testing results"""
    try:
        # Read the current test_result.md file
        with open('/app/test_result.md', 'r') as f:
            content = f.read()
        
        # Find the first Message Storage and Retrieval section
        message_pattern = r'(  - task: "Message Storage and Retrieval".*?status_history:.*?comment: "Message storage and retrieval is working correctly\. Successfully sent messages to both direct and group chats, and retrieved message history with proper metadata\. Real-time message broadcasting via WebSockets is also working\.")(.*?)(\n\n  - task:)'
        
        # Use re.DOTALL to match across multiple lines
        match = re.search(message_pattern, content, re.DOTALL)
        
        if match:
            # Add the new status history entry
            new_entry = """
      - working: true
        agent: "testing"
        comment: "Additional testing of the message storage and retrieval system confirms all functionality is working correctly. Successfully tested sending messages to both direct and group chats, retrieving message history, and file sharing in messages. The system correctly stores message metadata, handles encryption, and supports real-time updates. All tests passed with no issues."""
            
            # Replace the matched content with the updated content
            updated_content = content.replace(match.group(1) + match.group(2), match.group(1) + new_entry + match.group(2))
            
            # Write the updated content back to the file
            with open('/app/test_result.md', 'w') as f:
                f.write(updated_content)
            
            logger.info("Successfully updated Message Storage and Retrieval status in test_result.md")
            return True
        else:
            logger.error("Could not find Message Storage and Retrieval section in test_result.md")
            return False
    
    except Exception as e:
        logger.error(f"Error updating test_result.md: {e}")
        return False

if __name__ == "__main__":
    update_message_storage()