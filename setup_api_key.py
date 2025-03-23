#!/usr/bin/env python3
"""
Utility script to set up the AcoustID API key for the music recognition service.
This allows setting the API key without using the web interface.
"""

import os
import sys
import argparse

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
        print("Error: API key cannot be empty.")
        return False
    
    # Determine the file path based on the location
    if location == 'local':
        key_file = '.acoustid_api_key'
    elif location == 'user':
        key_file = os.path.expanduser('~/.acoustid_api_key')
    elif location == 'system':
        key_file = '/etc/acoustid_api_key'
        # Check if we have permission to write to system location
        if not os.access(os.path.dirname(key_file), os.W_OK):
            print(f"Error: Cannot write to {key_file}. Try running with sudo or choose a different location.")
            return False
    else:
        print(f"Error: Invalid location '{location}'. Use 'local', 'user', or 'system'.")
        return False
    
    # Write the API key to the file
    try:
        with open(key_file, 'w') as f:
            f.write(api_key.strip())
        
        # Set appropriate permissions
        if location in ('user', 'system'):
            os.chmod(key_file, 0o600)  # Make the file readable only by the owner
        
        print(f"AcoustID API key has been saved to {key_file}")
        return True
    except Exception as e:
        print(f"Error saving API key: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Set up the AcoustID API key for music recognition')
    parser.add_argument('api_key', help='Your AcoustID API key from https://acoustid.org/')
    parser.add_argument('--location', choices=['local', 'user', 'system'], default='local',
                       help='Where to store the API key: in the current directory (local), ' +
                            'user\'s home directory (user), or system-wide (system)')
    
    args = parser.parse_args()
    
    if setup_api_key(args.api_key, args.location):
        print("API key setup complete.")
        sys.exit(0)
    else:
        print("API key setup failed.")
        sys.exit(1)

if __name__ == '__main__':
    main()