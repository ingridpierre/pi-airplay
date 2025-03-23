#!/usr/bin/env python3
"""
A utility script to help update the development log with new entries.
This can be used by AI assistants or developers to maintain a consistent log.
"""

import os
import sys
from datetime import datetime
import re

LOG_FILE = "development_log.md"

def read_log():
    """Read the current log file."""
    if not os.path.exists(LOG_FILE):
        print(f"Error: {LOG_FILE} not found.")
        return None
    
    with open(LOG_FILE, 'r') as f:
        return f.read()

def append_entry(content, date=None):
    """Append a new dated entry to the log."""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    log_content = read_log()
    if log_content is None:
        return False
    
    # Check if an entry for today already exists
    date_pattern = f"### [{date}]"
    if date_pattern in log_content:
        # Update existing entry
        sections = re.split(r'(### \[\d{4}-\d{2}-\d{2}\].*?)(?=### \[|## |\Z)', log_content, flags=re.DOTALL)
        for i in range(len(sections)):
            if date_pattern in sections[i]:
                # Append to this section
                # Check if content already has bullet points
                if not content.strip().startswith("-"):
                    content = "- " + content
                sections[i] = sections[i].rstrip() + "\n" + content + "\n\n"
                break
        
        updated_content = ''.join(sections)
    else:
        # Create new entry in the Development History section
        history_section = "## Development History"
        if history_section not in log_content:
            print("Error: Could not find Development History section.")
            return False
        
        # Insert after the Development History heading
        parts = log_content.split(history_section, 1)
        updated_content = parts[0] + history_section + "\n\n"
        # Check if content already has bullet points
        if not content.strip().startswith("-"):
            content = "- " + content
        updated_content += f"### [{date}] New Updates\n{content}\n\n"
        if len(parts) > 1:
            updated_content += parts[1]
    
    # Write back to file
    with open(LOG_FILE, 'w') as f:
        f.write(updated_content)
    
    return True

def update_future_enhancements(enhancements):
    """Update the Future Enhancements section."""
    log_content = read_log()
    if log_content is None:
        return False
    
    future_section = "## Future Enhancements"
    if future_section not in log_content:
        print("Error: Could not find Future Enhancements section.")
        return False
    
    # Replace the Future Enhancements section
    pattern = r"## Future Enhancements\n.*?(?=\n## |$)"
    updated_content = re.sub(pattern, f"## Future Enhancements\n{enhancements}", log_content, flags=re.DOTALL)
    
    # Write back to file
    with open(LOG_FILE, 'w') as f:
        f.write(updated_content)
    
    return True

def add_design_decision(decision):
    """Add a new design decision to the Design Decisions section."""
    log_content = read_log()
    if log_content is None:
        return False
    
    section = "## Design Decisions"
    if section not in log_content:
        print("Error: Could not find Design Decisions section.")
        return False
    
    # Find the Design Decisions section and append
    parts = log_content.split(section, 1)
    section_content = parts[1].split("##", 1)[0] if "##" in parts[1] else parts[1]
    
    # Append the new decision
    updated_section = section_content.rstrip() + "\n- " + decision + "\n"
    
    # Reconstruct the document
    if "##" in parts[1]:
        updated_content = parts[0] + section + updated_section + "##" + parts[1].split("##", 1)[1]
    else:
        updated_content = parts[0] + section + updated_section
    
    # Write back to file
    with open(LOG_FILE, 'w') as f:
        f.write(updated_content)
    
    return True

def main():
    """Process command line arguments and update the log accordingly."""
    if len(sys.argv) < 3:
        print("Usage:")
        print("  update_log.py entry 'Your log entry text'")
        print("  update_log.py enhancement 'Your enhancement idea'")
        print("  update_log.py decision 'Your design decision'")
        return
    
    action = sys.argv[1].lower()
    content = sys.argv[2]
    
    if action == "entry":
        if append_entry(content):
            print("Log entry added successfully.")
        else:
            print("Failed to add log entry.")
    elif action == "enhancement":
        if update_future_enhancements(content):
            print("Future enhancements updated successfully.")
        else:
            print("Failed to update future enhancements.")
    elif action == "decision":
        if add_design_decision(content):
            print("Design decision added successfully.")
        else:
            print("Failed to add design decision.")
    else:
        print(f"Unknown action: {action}")

if __name__ == "__main__":
    main()