#!/usr/bin/env python3
"""
Utility script to set up the AcoustID API key for the music recognition service.
This allows setting the API key without using the web interface.
"""

import os
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_api_key(api_key, location='local'):
    """
    Set up the AcoustID API key in the specified location.
    
    Args:
        api_key (str): The AcoustID API key
        location (str): Where to store the key: 'local', 'user', or 'system'
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not api_key or not api_key.strip():
        logger.error("API key cannot be empty")
        return False
    
    api_key = api_key.strip()
    
    try:
        if location == 'local':
            # Save in the current directory
            with open('.acoustid_api_key', 'w') as f:
                f.write(api_key)
            logger.info("API key saved to .acoustid_api_key in the current directory")
            
        elif location == 'user':
            # Save in the user's home directory
            home_dir = os.path.expanduser('~')
            key_path = os.path.join(home_dir, '.acoustid_api_key')
            with open(key_path, 'w') as f:
                f.write(api_key)
            logger.info(f"API key saved to {key_path}")
            
        elif location == 'system':
            # Save in the system-wide location
            try:
                with open('/etc/acoustid_api_key', 'w') as f:
                    f.write(api_key)
                logger.info("API key saved to /etc/acoustid_api_key")
                
                # Make it readable by all users
                os.chmod('/etc/acoustid_api_key', 0o644)
            except PermissionError:
                logger.error("Permission denied. Run with sudo to save to system location.")
                return False
                
        else:
            logger.error(f"Invalid location: {location}")
            return False
            
        # Also set environment variable for current session
        os.environ['ACOUSTID_API_KEY'] = api_key
        logger.info("API key set as environment variable ACOUSTID_API_KEY")
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving API key: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Set up the AcoustID API key for Pi-DAD')
    parser.add_argument('api_key', help='The AcoustID API key')
    parser.add_argument('--location', choices=['local', 'user', 'system'], 
                        default='local', help='Where to store the API key')
    
    args = parser.parse_args()
    
    if setup_api_key(args.api_key, args.location):
        print("API key set up successfully.")
    else:
        print("Failed to set up API key.")
        exit(1)

if __name__ == '__main__':
    main()