"""
# src/main.py
# Main entry point for the Gmail Flight Tracker
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import argparse

from auth.google_auth import GoogleAuthManager
from auth.gmail_client import GmailClient
from parsers.flight_parser import FlightParser

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/flight_tracker.log')
    ]
)
logger = logging.getLogger(__name__)

class FlightTracker:
    def __init__(self, config_path: str = "config/accounts.json", year: Optional[int] = None):
        """Initialize the flight tracker with configuration."""
        logger.info("Initializing FlightTracker")
        self.config_path = Path(config_path)
        self.auth_manager = GoogleAuthManager()
        self.flight_parser = FlightParser()
        self.year = year
        self.accounts = self._load_accounts()
        
        # Create required directories
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        logger.info(f"FlightTracker initialized with year filter: {year if year else 'None'}")

    def _load_accounts(self) -> List[Dict[str, Any]]:
        """Load account configurations from the config file."""
        try:
            logger.info(f"Loading accounts from {self.config_path}")
            with open(self.config_path) as f:
                accounts = json.load(f)
            logger.info(f"Successfully loaded {len(accounts)} account(s)")
            return accounts
        except FileNotFoundError:
            logger.error(f"Config file not found at {self.config_path}")
            return []
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in config file {self.config_path}")
            return []

    def process_account(self, account: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process emails from a single account."""
        account_id = account['account_id']
        logger.info(f"Processing account: {account_id}")
        
        try:
            # Get credentials and create Gmail client
            logger.debug(f"Getting credentials for account {account_id}")
            credentials = self.auth_manager.get_credentials(account_id)
            gmail_client = GmailClient(credentials)
            
            # Build search query
            query = "subject:(flight OR itinerary OR booking OR reservation OR e-ticket)"
            
            # Add year filter if specified
            if self.year:
                start_date = f"{self.year}/01/01"
                end_date = f"{self.year}/12/31"
                query += f" after:{start_date} before:{end_date}"
            elif account.get('last_processed_date'):
                query += f" after:{account['last_processed_date']}"
            
            logger.info(f"Searching emails with query: {query}")
            messages = gmail_client.search_messages(query)
            logger.info(f"Found {len(messages)} matching emails")
            
            flight_data = []
            processed_count = 0
            
            for msg in messages:
                processed_count += 1
                if processed_count % 10 == 0:  # Log progress every 10 messages
                    logger.info(f"Processing message {processed_count}/{len(messages)}")
                
                message_detail = gmail_client.get_message(msg['id'])
                if not message_detail:
                    logger.warning(f"Could not fetch details for message {msg['id']}")
                    continue
                
                content = gmail_client.parse_message_content(message_detail)
                content['id'] = msg['id']
                
                flight_info = self.flight_parser.parse_email(content)
                if flight_info:
                    logger.debug(f"Successfully extracted flight info: {flight_info['flight_number']}")
                    flight_info['account_id'] = account_id
                    flight_data.append(flight_info)
                else:
                    logger.debug(f"No flight information found in message {msg['id']}")
            
            logger.info(f"Successfully processed {len(flight_data)} flights from {len(messages)} emails")
            return flight_data
            
        except Exception as e:
            logger.error(f"Error processing account {account_id}: {e}", exc_info=True)
            return []

    def process_all_accounts(self) -> None:
        """Process all configured accounts and save the results."""
        logger.info("Starting to process all accounts")
        all_flight_data = []
        
        for account in self.accounts:
            flight_data = self.process_account(account)
            all_flight_data.extend(flight_data)
        
        if all_flight_data:
            self._save_flight_data(all_flight_data)
            if not self.year:  # Only update last processed date if not filtering by year
                self._update_last_processed_dates()
        
        logger.info(f"Completed processing with {len(all_flight_data)} total flights found")

    def _save_flight_data(self, flight_data: List[Dict[str, Any]]) -> None:
        """Save flight data to CSV and JSON formats."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        year_suffix = f"_{self.year}" if self.year else ""
        
        # Save as JSON
        json_path = self.data_dir / f"flights{year_suffix}_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(flight_data, f, indent=2)
        
        # Save as CSV
        df = pd.DataFrame(flight_data)
        csv_path = self.data_dir / f"flights{year_suffix}_{timestamp}.csv"
        df.to_csv(csv_path, index=False)
        
        logger.info(f"Saved flight data to {json_path} and {csv_path}")

    def _update_last_processed_dates(self) -> None:
        """Update the last processed date for each account."""
        logger.info("Updating last processed dates")
        current_date = datetime.now().strftime("%Y/%m/%d")
        
        for account in self.accounts:
            account['last_processed_date'] = current_date
        
        with open(self.config_path, 'w') as f:
            json.dump(self.accounts, f, indent=2)
        logger.info("Successfully updated last processed dates")

def main():
    """Main entry point for the flight tracker."""
    try:
        # Set up argument parser
        parser = argparse.ArgumentParser(description='Gmail Flight Tracker')
        parser.add_argument('--year', type=int, help='Year to filter flight data (e.g., 2023)')
        parser.add_argument('--debug', action='store_true', help='Enable debug logging')
        args = parser.parse_args()

        # Set debug logging if requested
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug logging enabled")

        logger.info(f"Starting Gmail Flight Tracker{' for year ' + str(args.year) if args.year else ''}")
        tracker = FlightTracker(year=args.year)
        tracker.process_all_accounts()
        logger.info("Gmail Flight Tracker completed successfully")
    except Exception as e:
        logger.error(f"Error running flight tracker: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
