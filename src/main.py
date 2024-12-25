"""
# src/main.py
# Main entry point for the Gmail Flight Tracker
"""

import argparse
from datetime import datetime, timedelta
import json
import os
from typing import List, Dict
from parsers.flight_parser import parse_flight_email, format_flight_details
from gmail_client import fetch_flight_emails
import re

def process_emails(emails: List[Dict]) -> List[Dict]:
    """Process emails and extract flight information"""
    flight_info_list = []
    
    for email in emails:
        print(f"\nProcessing email: {email.get('subject')}")
        flight_info = parse_flight_email(email)
        if flight_info:
            flight_dict = flight_info.to_dict()
            print("Extracted flight info:")
            print(format_flight_details(flight_dict))
            flight_info_list.append(flight_dict)
        else:
            print("No flight information extracted")
    
    # Remove duplicates
    return deduplicate_flights(flight_info_list)

def deduplicate_flights(flights: List[Dict]) -> List[Dict]:
    """Remove duplicate flight entries based on key fields"""
    unique_flights = {}
    
    for flight in flights:
        # Create a unique key based on flight details
        key_parts = []
        
        # Required fields for a valid flight entry
        if flight.get('flight_number') and flight.get('departure_datetime'):
            key_parts.extend([
                flight.get('flight_number'),
                flight.get('departure_datetime', '').split('T')[0]
            ])
            
            # Optional fields that help identify unique flights
            key_parts.extend([
                flight.get('departure_airport', ''),
                flight.get('arrival_airport', '')
            ])
            
            key = tuple(key_parts)
            
            # Keep the entry with the most information
            if key not in unique_flights or _count_filled_fields(flight) > _count_filled_fields(unique_flights[key]):
                unique_flights[key] = flight
    
    # Sort flights by departure datetime
    sorted_flights = sorted(
        unique_flights.values(),
        key=lambda x: x.get('departure_datetime', '') or ''
    )
    
    return sorted_flights

def _count_filled_fields(flight: Dict) -> int:
    """Count the number of non-None fields in a flight entry"""
    return sum(1 for value in flight.values() if value is not None)

def main():
    parser = argparse.ArgumentParser(description='Gmail Flight Tracker')
    parser.add_argument('--year', type=int, default=datetime.now().year,
                      help='Year to search for flights (default: current year)')
    parser.add_argument('--days', type=int, default=365,
                      help='Number of days to look forward from start of year')
    parser.add_argument('--use-sample', action='store_true',
                      help='Use sample data instead of Gmail API')
    args = parser.parse_args()
    
    print(f"Loading emails for {args.year} (looking forward {args.days} days from start of year)...")
    
    if args.use_sample:
        # Load sample data
        sample_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sample')
        if not os.path.exists(sample_dir):
            print(f"Error: Sample directory not found at {sample_dir}")
            return
            
        emails = []
        start_date = datetime(args.year, 1, 1)
        end_date = start_date + timedelta(days=args.days)
        print(f"Looking for emails between {start_date.date()} and {end_date.date()}")
        
        for filename in os.listdir(sample_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(sample_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        email_data = json.load(f)
                        
                        # Parse email date
                        email_date = datetime.strptime(email_data.get('date', ''), '%a, %d %b %Y %H:%M:%S %z')
                        
                        # Extract flight date from body for more accurate filtering
                        body = email_data.get('body', '')
                        flight_date = None
                        
                        # Try to find flight date in common formats
                        date_patterns = [
                            r'(\w+ \d{1,2}, \d{4})\s*\|',  # March 19, 2024 |
                            r'Flight Date:?\s*(\w+ \d{1,2},? \d{4})',  # Flight Date: March 19, 2024
                            r'Departure:?\s*(\w+ \d{1,2},? \d{4})',  # Departure: March 19, 2024
                            r'(\d{2}/\d{2}/\d{4})'  # 15/02/2024
                        ]
                        
                        for pattern in date_patterns:
                            match = re.search(pattern, body)
                            if match:
                                try:
                                    date_str = match.group(1)
                                    if '/' in date_str:
                                        flight_date = datetime.strptime(date_str, '%d/%m/%Y')
                                    else:
                                        flight_date = datetime.strptime(date_str, '%B %d, %Y')
                                    break
                                except ValueError:
                                    continue
                        
                        # Use flight date if found, otherwise use email date
                        check_date = flight_date.replace(tzinfo=None) if flight_date else email_date.replace(tzinfo=None)
                        
                        # Check if date is within range
                        if start_date <= check_date <= end_date:
                            print(f"Found matching email: {email_data.get('subject')} (Date: {check_date.date()})")
                            emails.append(email_data)
                except Exception as e:
                    print(f"Error loading {filename}: {str(e)}")
                    continue
        
        print(f"Found {len(emails)} emails in the specified date range")
    else:
        # Use Gmail API
        emails = fetch_flight_emails(args.year, args.days)
    
    print("\nProcessing emails...")
    flights = process_emails(emails)
    
    if flights:
        print(f"\nFound {len(flights)} unique flights:\n")
        for i, flight in enumerate(flights, 1):
            print(f"Flight {i}:")
            print("-" * 40)
            print(format_flight_details(flight))
            print()
    else:
        print("\nNo flight information found in the specified date range.")

if __name__ == '__main__':
    main()
