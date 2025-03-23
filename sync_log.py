#!/usr/bin/env python3
"""
Utility to sync the development log with other AI assistant windows.
This script extracts the most recent entries from the development log
to provide a concise summary of recent changes.
"""

import re
import sys
from datetime import datetime, timedelta

LOG_FILE = "development_log.md"

def read_log():
    """Read the current log file."""
    try:
        with open(LOG_FILE, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: {LOG_FILE} not found.")
        return None

def extract_recent_entries(days=7):
    """Extract entries from the last N days."""
    log_content = read_log()
    if log_content is None:
        return None
    
    # Calculate the date N days ago
    today = datetime.now()
    cutoff_date = today - timedelta(days=days)
    cutoff_str = cutoff_date.strftime('%Y-%m-%d')
    
    # Extract all dated entries
    date_pattern = r'### \[(\d{4}-\d{2}-\d{2})\](.*?)(?=### \[|## |\Z)'
    entries = re.findall(date_pattern, log_content, re.DOTALL)
    
    # Filter to only include recent entries
    recent_entries = []
    for date_str, content in entries:
        if date_str >= cutoff_str:
            recent_entries.append((date_str, content.strip()))
    
    return recent_entries

def extract_design_decisions():
    """Extract the design decisions section."""
    log_content = read_log()
    if log_content is None:
        return None
    
    section_pattern = r'## Design Decisions\n(.*?)(?=\n## |$)'
    match = re.search(section_pattern, log_content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def extract_future_enhancements():
    """Extract the future enhancements section."""
    log_content = read_log()
    if log_content is None:
        return None
    
    section_pattern = r'## Future Enhancements\n(.*?)(?=\n## |$)'
    match = re.search(section_pattern, log_content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def generate_sync_summary(days=7):
    """Generate a summary of recent changes for syncing."""
    recent_entries = extract_recent_entries(days)
    design_decisions = extract_design_decisions()
    future_enhancements = extract_future_enhancements()
    
    if recent_entries is None:
        return "Error reading development log."
    
    summary = "# Development Log Sync\n\n"
    summary += f"## Recent Updates (Last {days} Days)\n\n"
    
    if not recent_entries:
        summary += "No updates in the specified timeframe.\n\n"
    else:
        for date_str, content in recent_entries:
            summary += f"### [{date_str}]\n{content}\n\n"
    
    if design_decisions:
        summary += "## Key Design Decisions\n\n"
        summary += design_decisions + "\n\n"
    
    if future_enhancements:
        summary += "## Planned Enhancements\n\n"
        summary += future_enhancements + "\n\n"
    
    return summary

def main():
    """Process command line arguments and generate the sync summary."""
    days = 7  # Default to last 7 days
    
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print("Error: Days parameter must be an integer.")
            return
    
    summary = generate_sync_summary(days)
    print(summary)

if __name__ == "__main__":
    main()