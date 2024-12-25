"""
# src/parsers/flight_parser.py
# Parser for extracting flight information from email content
"""

import re
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class FlightParser:
    # Common patterns for flight information
    PATTERNS = {
        'flight_number': r'(?:Flight|FLT)\s*(?:#|:|\s)\s*([A-Z]{2,3}\s*\d{1,4})',
        'airports': r'(?:from|From|FROM)\s+([A-Z]{3}).*?(?:to|To|TO)\s+([A-Z]{3})',
        'date': r'(?:Date|DATE|date):\s*(\w+\s+\d{1,2},?\s+\d{4})',
        'time': r'(?:Time|TIME|time):\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)',
        'confirmation': r'(?:Confirmation|CONFIRMATION|confirmation|Booking|Reference)\s*(?:#|:|\s)\s*([A-Z0-9]{6,8})',
    }

    def __init__(self):
        """Initialize the flight parser with compiled regex patterns."""
        self.compiled_patterns = {
            key: re.compile(pattern) for key, pattern in self.PATTERNS.items()
        }

    def parse_email(self, email_content: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse flight information from email content."""
        try:
            subject = email_content['subject']
            body = email_content['body']
            sender = email_content['from']
            date = email_content['date']

            # Skip if not likely a flight email
            if not self._is_flight_email(subject, sender):
                return None

            flight_info = {
                'email_subject': subject,
                'email_date': date,
                'email_sender': sender,
                'source_email_id': email_content.get('id', ''),
                'extracted_date': datetime.now().isoformat(),
            }

            # Extract information using patterns
            text_to_search = f"{subject}\n{body}"
            
            # Extract flight number
            flight_match = self.compiled_patterns['flight_number'].search(text_to_search)
            if flight_match:
                flight_info['flight_number'] = flight_match.group(1).replace(' ', '')

            # Extract airports
            airports_match = self.compiled_patterns['airports'].search(text_to_search)
            if airports_match:
                flight_info['departure_airport'] = airports_match.group(1)
                flight_info['arrival_airport'] = airports_match.group(2)

            # Extract date
            date_match = self.compiled_patterns['date'].search(text_to_search)
            if date_match:
                flight_info['flight_date'] = date_match.group(1)

            # Extract time
            time_match = self.compiled_patterns['time'].search(text_to_search)
            if time_match:
                flight_info['flight_time'] = time_match.group(1)

            # Extract confirmation number
            conf_match = self.compiled_patterns['confirmation'].search(text_to_search)
            if conf_match:
                flight_info['confirmation_number'] = conf_match.group(1)

            # Validate extracted information
            if self._is_valid_flight_info(flight_info):
                return flight_info
            return None

        except Exception as e:
            logger.error(f"Error parsing flight email: {e}")
            return None

    def _is_flight_email(self, subject: str, sender: str) -> bool:
        """Check if the email is likely a flight-related email."""
        flight_keywords = [
            'flight', 'itinerary', 'booking', 'reservation', 'travel', 
            'e-ticket', 'eticket', 'confirmation'
        ]
        airline_domains = [
            'united.com', 'aa.com', 'delta.com', 'southwest.com',
            'alaskaair.com', 'spirit.com', 'jetblue.com'
        ]

        subject_lower = subject.lower()
        if any(keyword in subject_lower for keyword in flight_keywords):
            return True

        sender_lower = sender.lower()
        if any(domain in sender_lower for domain in airline_domains):
            return True

        return False

    def _is_valid_flight_info(self, flight_info: Dict[str, Any]) -> bool:
        """Validate that the extracted flight information is sufficient."""
        required_fields = ['flight_number', 'departure_airport', 'arrival_airport']
        return all(field in flight_info for field in required_fields) 