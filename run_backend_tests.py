#!/usr/bin/env python3
import subprocess
import logging
import os
import sys
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_test_script(script_name):
    """Run a test script and return True if all tests pass"""
    logger.info(f"Running test script: {script_name}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=False,
            capture_output=True,
            text=True
        )
        
        # Log the output
        for line in result.stdout.splitlines():
            logger.info(line)
        
        # Check for errors
        if result.stderr:
            for line in result.stderr.splitlines():
                logger.error(line)
        
        # Check if tests passed
        if "OVERALL RESULT: PASSED" in result.stdout:
            logger.info(f"{script_name} tests PASSED")
            return True
        else:
            logger.error(f"{script_name} tests FAILED")
            return False
    
    except Exception as e:
        logger.error(f"Error running {script_name}: {e}")
        return False

def main():
    """Run all test scripts"""
    logger.info("Starting comprehensive backend testing...")
    
    # Define test scripts for each phase
    test_scripts = [
        # Phase 1: Teams Chat Functionality
        "/app/teams_chat_test.py",
        
        # Phase 2: Voice/Video Calling
        "/app/voice_video_call_test.py",
        
        # Phase 3: Enhanced File Sharing
        "/app/enhanced_file_sharing_test.py"
    ]
    
    # Run each test script
    results = {}
    all_passed = True
    
    for script in test_scripts:
        if os.path.exists(script):
            result = run_test_script(script)
            results[script] = result
            if not result:
                all_passed = False
        else:
            logger.error(f"Test script not found: {script}")
            results[script] = False
            all_passed = False
    
    # Print summary
    logger.info("\n\n" + "=" * 80)
    logger.info("COMPREHENSIVE BACKEND TEST RESULTS SUMMARY")
    logger.info("=" * 80)
    
    for script, result in results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{os.path.basename(script)}: {status}")
    
    logger.info("=" * 80)
    logger.info(f"OVERALL RESULT: {'PASSED' if all_passed else 'FAILED'}")
    logger.info("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    main()