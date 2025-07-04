import json
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_file_upload():
    """Update the test_result.md file with File Upload API testing results"""
    try:
        # Read the current test_result.md file
        with open('/app/test_result.md', 'r') as f:
            content = f.read()
        
        # Find the first File Upload API section
        file_pattern = r'(  - task: "File Upload API".*?status_history:.*?comment: "File upload API is working correctly\. Successfully tested uploading image files, file size validation \(rejecting files >10MB\), and file type validation\. The API correctly returns file metadata including name, size, type, and base64-encoded data\.")(.*?)(\n\n  - task:)'
        
        # Use re.DOTALL to match across multiple lines
        match = re.search(file_pattern, content, re.DOTALL)
        
        if match:
            # Add the new status history entry
            new_entry = """
      - working: true
        agent: "testing"
        comment: "Additional testing of the file upload API confirms all functionality is working correctly. Successfully tested uploading different file types, integrating uploaded files into messages, and retrieving files from message history. The API correctly handles file metadata and content encoding. All tests passed with no issues."""
            
            # Replace the matched content with the updated content
            updated_content = content.replace(match.group(1) + match.group(2), match.group(1) + new_entry + match.group(2))
            
            # Write the updated content back to the file
            with open('/app/test_result.md', 'w') as f:
                f.write(updated_content)
            
            logger.info("Successfully updated File Upload API status in test_result.md")
            return True
        else:
            logger.error("Could not find File Upload API section in test_result.md")
            return False
    
    except Exception as e:
        logger.error(f"Error updating test_result.md: {e}")
        return False

if __name__ == "__main__":
    update_file_upload()