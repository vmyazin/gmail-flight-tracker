"""
# src/parsers/flight_parser.py
# Parser for extracting flight information from email content
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import json
import pytz

class FlightInfo:
    def __init__(self):
        self.flight_number: str = None
        self.departure_airport: str = None
        self.arrival_airport: str = None
        self.departure_datetime: datetime = None
        self.arrival_datetime: datetime = None
        self.airline: str = None
        self.duration: str = None

    def to_dict(self) -> Dict:
        return {
            'flight_number': self.flight_number,
            'departure_airport': self.departure_airport,
            'arrival_airport': self.arrival_airport,
            'departure_datetime': self.departure_datetime.isoformat() if self.departure_datetime else None,
            'arrival_datetime': self.arrival_datetime.isoformat() if self.arrival_datetime else None,
            'airline': self.airline,
            'duration': self.duration
        }

class BaseFlightParser:
    """Base class for all airline-specific parsers"""
    
    AIRPORT_CODE_PATTERN = r'\b([A-Z]{3})\b'
    FLIGHT_NUMBER_PATTERN = r'\b([A-Z0-9]{2})\s*(\d{1,4})\b'
    
    def __init__(self):
        self.flight_info = FlightInfo()

    def parse_email(self, email_data: Dict) -> Optional[FlightInfo]:
        """Parse email data and return FlightInfo object"""
        raise NotImplementedError("Subclasses must implement parse_email method")

    def _extract_airport_codes(self, text: str) -> List[str]:
        """Extract airport codes from text"""
        return re.findall(self.AIRPORT_CODE_PATTERN, text)

    def _extract_flight_number(self, text: str) -> Optional[str]:
        """Extract flight number from text"""
        match = re.search(self.FLIGHT_NUMBER_PATTERN, text)
        if match:
            return f"{match.group(1)}{match.group(2)}"
        return None

    def _parse_datetime(self, date_str: str, time_str: str, timezone: str = None) -> Optional[datetime]:
        """Parse date and time strings into datetime object"""
        try:
            # Common date formats
            date_formats = [
                '%B %d, %Y',     # December 25, 2024
                '%d %B %Y',      # 25 December 2024
                '%Y-%m-%d',      # 2024-12-25
                '%d/%m/%Y',      # 25/12/2024
                '%b %d, %Y',     # Dec 25, 2024
                '%d %b %Y',      # 25 Dec 2024
                '%d %b'          # 25 Dec (current year)
            ]
            
            parsed_date = None
            for fmt in date_formats:
                try:
                    if '%Y' not in fmt:
                        # Add current year for formats without year
                        current_year = datetime.now().year
                        parsed_date = datetime.strptime(f"{date_str} {current_year}", f"{fmt} %Y")
                    else:
                        parsed_date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            
            if not parsed_date:
                return None
            
            # Parse time
            try:
                time_parts = list(map(int, time_str.split(':')))
                parsed_date = parsed_date.replace(hour=time_parts[0], minute=time_parts[1])
            except (ValueError, IndexError):
                return None
            
            return parsed_date
        except Exception:
            return None

    def _calculate_arrival_time(self, departure: datetime, duration_str: str) -> Optional[datetime]:
        """Calculate arrival time based on departure time and duration"""
        if not departure or not duration_str:
            return None
            
        try:
            hours, minutes = map(int, duration_str.split(':'))
            return departure + timedelta(hours=hours, minutes=minutes)
        except (ValueError, TypeError):
            return None

class VietJetParser(BaseFlightParser):
    """Parser for VietJet Air flight emails"""
    
    def parse_email(self, email_data: Dict) -> Optional[FlightInfo]:
        body = email_data.get('body', '')
        subject = email_data.get('subject', '')
        
        # Set airline
        self.flight_info.airline = "VietJet Air"
        
        # Extract booking reference from both formats
        booking_patterns = [
            r'Reservation #:\s*(\d+)',  # Format: Reservation #:    168470326
            r'#([A-Z0-9]{6})'  # Format: #6Q3PSU
        ]
        for pattern in booking_patterns:
            booking_ref_match = re.search(pattern, body) or re.search(pattern, subject)
            if booking_ref_match:
                self.flight_info.booking_reference = booking_ref_match.group(1)
                break
        
        # Extract passenger name
        name_patterns = [
            r'Full Name:\s*([^\r\n]+)',  # Format: Full Name:        MYAZIN, VASILY
            r'Name:\s*([^\r\n]+)',       # Format: Name:     MYAZIN, VASILY
            r'Dear\s+([^,\n]+)'          # Format: Dear John Smith
        ]
        for pattern in name_patterns:
            name_match = re.search(pattern, body)
            if name_match:
                name = name_match.group(1).strip()
                if name.lower() != 'our valued customer':
                    self.flight_info.passenger_name = name
                    break
        
        # Extract flight details
        # First try to find the flight information section
        if 'FLIGHT INFORMATION' in body:
            # Split the body at FLIGHT INFORMATION and take the part after the header line
            flight_section = body.split('FLIGHT INFORMATION')[1].split('\n\n')[0]
            
            # Extract flight details from the table format
            # Format: VZ350               15/02/2024  09:35 - BangKok - Suvarnabhu                                 10:50 - Surat Thani                                          Economy
            flight_pattern = r'([A-Z]{2}\d{3})\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})\s*-\s*([^-]+)-([^-]+)-?\s*(\d{2}:\d{2})\s*-\s*([^-\n]+?)(?:\s+([A-Za-z]+)\s*)?$'
            
            flight_match = re.search(flight_pattern, flight_section, re.MULTILINE)
            if flight_match:
                # Flight number
                self.flight_info.flight_number = flight_match.group(1)
                
                # Date and times
                date_str = flight_match.group(2)
                dep_time = flight_match.group(3)
                arr_time = flight_match.group(6)
                
                try:
                    # Parse departure datetime
                    departure_dt = datetime.strptime(f"{date_str} {dep_time}", "%d/%m/%Y %H:%M")
                    self.flight_info.departure_datetime = departure_dt
                    
                    # Parse arrival datetime (same day)
                    arrival_dt = datetime.strptime(f"{date_str} {arr_time}", "%d/%m/%Y %H:%M")
                    self.flight_info.arrival_datetime = arrival_dt
                    
                    # Calculate duration
                    duration = arrival_dt - departure_dt
                    hours, remainder = divmod(duration.seconds, 3600)
                    minutes = remainder // 60
                    self.flight_info.duration = f"{hours}:{minutes:02d}"
                except ValueError:
                    pass
                
                # Extract airports
                dep_airport = flight_match.group(4).strip()
                arr_airport = flight_match.group(7).strip()
                
                # Try to find airport codes
                airport_codes = re.findall(r'\b([A-Z]{3})\b', flight_section)
                if len(airport_codes) >= 2:
                    self.flight_info.departure_airport = airport_codes[0]
                    self.flight_info.arrival_airport = airport_codes[1]
                else:
                    # Clean and use airport names if codes not found
                    dep_airport = re.sub(r'\s+', ' ', dep_airport).strip()
                    arr_airport = re.sub(r'\s+', ' ', arr_airport).strip()
                    self.flight_info.departure_airport = dep_airport
                    self.flight_info.arrival_airport = arr_airport
                
                # Extract cabin class
                if flight_match.group(8):
                    self.flight_info.cabin_class = flight_match.group(8)
                else:
                    self.flight_info.cabin_class = 'Economy'
        else:
            # Try notification email format
            flight_pattern = r'(\w+\s+\d{1,2},\s*\d{4})\s*(\d{1,2}:\d{2})\s*([A-Z]{3})\s*-\s*([A-Z]{3})'
            flight_match = re.search(flight_pattern, body)
            
            if flight_match:
                date_str = flight_match.group(1)
                time_str = flight_match.group(2)
                self.flight_info.departure_airport = flight_match.group(3)
                self.flight_info.arrival_airport = flight_match.group(4)
                self.flight_info.departure_datetime = self._parse_datetime(date_str, time_str)
                
                # Try to extract flight number from subject or body
                flight_num_match = re.search(r'VZ\s*(\d{3,4})', body)
                if flight_num_match:
                    self.flight_info.flight_number = f"VZ{flight_num_match.group(1)}"
        
        # Only return flight info if we have the minimum required fields
        if (self.flight_info.flight_number and self.flight_info.departure_datetime) or \
           (self.flight_info.departure_airport and self.flight_info.arrival_airport and self.flight_info.departure_datetime):
            return self.flight_info
        return None

class TripComParser(BaseFlightParser):
    """Parser for Trip.com flight emails"""
    
    def parse_email(self, email_data: Dict) -> Optional[FlightInfo]:
        body = email_data.get('body', '')
        subject = email_data.get('subject', '')
        
        # Extract booking reference
        booking_ref_match = re.search(r'Booking No\.[:：]\s*(\w+)', body)
        if booking_ref_match:
            self.flight_info.booking_reference = booking_ref_match.group(1)

        # Extract passenger name
        name_match = re.search(r'(\w+)\s*\(Given names\)\s*(\w+)\s*\(Surname\)', body)
        if name_match:
            self.flight_info.passenger_name = f"{name_match.group(2)}, {name_match.group(1)}"

        # Extract flight details
        flight_section_match = re.search(r'(\w+\s+\d+,\s+\d{4})\s*\|\s*([^-]+)-\s*([^\n]+)\n(\d{1,2}:\d{2})[^\n]*\n([^\n•]+)([^\n]*)', body)
        if flight_section_match:
            date_str = flight_section_match.group(1)
            dep_airport = flight_section_match.group(2).strip()
            arr_airport = flight_section_match.group(3).strip()
            time_str = flight_section_match.group(4)
            airline_info = flight_section_match.group(5).strip()
            
            # Extract airport codes
            airports = self._extract_airport_codes(body)
            if len(airports) >= 2:
                self.flight_info.departure_airport = airports[0]
                self.flight_info.arrival_airport = airports[1]

            # Extract flight number
            self.flight_info.flight_number = self._extract_flight_number(airline_info)
            
            # Extract airline
            self.flight_info.airline = airline_info.split()[0]

            # Parse departure datetime
            self.flight_info.departure_datetime = self._parse_datetime(date_str, time_str)

            # Extract duration
            duration_match = re.search(r'(\d+)hr\s+(\d+)mins', body)
            if duration_match:
                self.flight_info.duration = f"{duration_match.group(1)}:{duration_match.group(2)}"
                
            # Calculate arrival time
            if self.flight_info.departure_datetime and self.flight_info.duration:
                self.flight_info.arrival_datetime = self._calculate_arrival_time(
                    self.flight_info.departure_datetime,
                    self.flight_info.duration
                )

            # Extract cabin class
            if 'Economy' in body:
                self.flight_info.cabin_class = 'Economy'
            elif 'Business' in body:
                self.flight_info.cabin_class = 'Business'
            elif 'First' in body:
                self.flight_info.cabin_class = 'First'

        return self.flight_info

class BookingComParser(BaseFlightParser):
    """Parser for Booking.com flight emails"""
    
    def parse_email(self, email_data: Dict) -> Optional[FlightInfo]:
        body = email_data.get('body', '')
        subject = email_data.get('subject', '').lower()
        
        # Set airline
        self.flight_info.airline = None  # Will be extracted from flight details
        
        # Try different flight detail patterns
        flight_patterns = [
            # New format: Manila (MNL) to Da Nang (DAD) 7 Apr · 19:30 - 7 Apr · 21:30 Direct · 3h · Economy Cebu Air · 5J5756
            r'([^(]+)\(([A-Z]{3})\)\s+to\s+([^(]+)\(([A-Z]{3})\)\s+(\d{1,2}\s+[A-Za-z]{3})\s*·\s*(\d{1,2}:\d{2})\s*-\s*\d{1,2}\s+[A-Za-z]{3}\s*·\s*(\d{1,2}:\d{2})[^·]*·\s*(\d+)h[^·]*·\s*([^·]+)·\s*([^·]+)·\s*([A-Z0-9]+)',
            # Alternative format: MNL → DAD LHNTTZ
            r'([A-Z]{3})\s*[→→]\s*([A-Z]{3})\s+([A-Z0-9]+)',
            # Old format
            r'(\w+)\s*\(([A-Z]{3})\)\s*to\s*(\w+[^(]*)\s*\(([A-Z]{3})\)[^\n]*\n(\d{1,2}\s+\w+)\s*·\s*(\d{1,2}:\d{2})\s*-[^\n]*(\d{1,2}:\d{2})'
        ]
        
        for pattern in flight_patterns:
            flight_match = re.search(pattern, body)
            if flight_match:
                if '3h' in pattern:  # New format with full details
                    # Airports
                    self.flight_info.departure_airport = flight_match.group(2)  # MNL
                    self.flight_info.arrival_airport = flight_match.group(4)    # DAD
                    
                    # Date and times
                    date_str = flight_match.group(5)  # 7 Apr
                    dep_time = flight_match.group(6)  # 19:30
                    arr_time = flight_match.group(7)  # 21:30
                    
                    # Duration
                    duration_hours = flight_match.group(8)
                    self.flight_info.duration = f"{duration_hours}:00"
                    
                    # Cabin class and airline
                    self.flight_info.airline = flight_match.group(10).strip()     # Cebu Air
                    
                    # Flight number
                    self.flight_info.flight_number = flight_match.group(11)  # 5J5756
                    
                    # Parse datetime
                    try:
                        self.flight_info.departure_datetime = self._parse_datetime(date_str, dep_time)
                        
                        # Calculate arrival time
                        if self.flight_info.departure_datetime:
                            hours = int(duration_hours)
                            self.flight_info.arrival_datetime = self.flight_info.departure_datetime + timedelta(hours=hours)
                    except ValueError:
                        pass
                
                elif '→' in pattern:  # Simple format with just airports and reference
                    self.flight_info.departure_airport = flight_match.group(1)
                    self.flight_info.arrival_airport = flight_match.group(2)
                    
                    # Try to find flight details in a separate section
                    flight_details = re.search(
                        r'(\d{1,2}\s+[A-Za-z]{3})\s*·\s*(\d{1,2}:\d{2})[^·]*·\s*(\d+)h[^·]*·\s*[^·]+·\s*([^·]+)·\s*([A-Z0-9]+)',
                        body
                    )
                    if flight_details:
                        date_str = flight_details.group(1)
                        time_str = flight_details.group(2)
                        duration = flight_details.group(3)
                        self.flight_info.airline = flight_details.group(4).strip()
                        self.flight_info.flight_number = flight_details.group(5)
                        self.flight_info.duration = f"{duration}:00"
                        
                        try:
                            self.flight_info.departure_datetime = self._parse_datetime(date_str, time_str)
                            if self.flight_info.departure_datetime:
                                hours = int(duration)
                                self.flight_info.arrival_datetime = self.flight_info.departure_datetime + timedelta(hours=hours)
                        except ValueError:
                            pass
                    
                else:  # Old format
                    self.flight_info.departure_airport = flight_match.group(2)
                    self.flight_info.arrival_airport = flight_match.group(4)
                    
                    # Parse datetime
                    date_str = flight_match.group(5)
                    time_str = flight_match.group(6)
                    try:
                        self.flight_info.departure_datetime = self._parse_datetime(date_str, time_str)
                    except ValueError:
                        pass
                    
                    # Extract duration
                    duration_match = re.search(r'(\d+)h\s+(\d+)m', body)
                    if duration_match:
                        self.flight_info.duration = f"{duration_match.group(1)}:{duration_match.group(2)}"
                        
                        # Calculate arrival time
                        if self.flight_info.departure_datetime and self.flight_info.duration:
                            self.flight_info.arrival_datetime = self._calculate_arrival_time(
                                self.flight_info.departure_datetime,
                                self.flight_info.duration
                            )
                    
                    # Extract flight number and airline
                    flight_num_match = re.search(r'([A-Z0-9]{2})\s*(\d{1,4})', body)
                    if flight_num_match:
                        airline_code = flight_num_match.group(1)
                        flight_num = flight_num_match.group(2)
                        self.flight_info.flight_number = f"{airline_code}{flight_num}"
                        
                        # Map airline code to airline name
                        airline_map = {
                            '5J': 'Cebu Pacific',
                            'PR': 'Philippine Airlines',
                            'Z2': 'AirAsia Philippines',
                            'VZ': 'Thai Vietjet Air',
                            '10': 'Cebu Pacific'  # Alternative code for Cebu Pacific
                        }
                        self.flight_info.airline = airline_map.get(airline_code, airline_code)
                
                break
        
        # Only return flight info if we have the minimum required fields
        if (self.flight_info.flight_number and self.flight_info.departure_datetime) or \
           (self.flight_info.departure_airport and self.flight_info.arrival_airport and self.flight_info.departure_datetime):
            return self.flight_info
        return None

def parse_flight_email(email_data: Dict) -> Optional[FlightInfo]:
    """
    Main entry point for parsing flight emails.
    Determines the appropriate parser based on email metadata and returns flight information.
    """
    from_address = email_data.get('from', '').lower()
    subject = email_data.get('subject', '').lower()
    
    if 'vietjet' in from_address or 'vietjet' in subject:
        parser = VietJetParser()
    elif 'trip.com' in from_address:
        parser = TripComParser()
    elif 'booking.com' in from_address:
        parser = BookingComParser()
    else:
        return None  # Unsupported email format
    
    return parser.parse_email(email_data)

def format_flight_details(flight: Dict) -> str:
    """Format flight details for display"""
    # Define the order and labels for fields
    field_order = [
        ('flight_number', 'Flight'),
        ('airline', 'Airline'),
        ('departure_airport', 'From'),
        ('arrival_airport', 'To'),
        ('departure_datetime', 'Departure'),
        ('arrival_datetime', 'Arrival'),
        ('duration', 'Duration')
    ]
    
    # Format each field
    lines = []
    for field, label in field_order:
        value = flight.get(field)
        if value:
            if field.endswith('_datetime'):
                # Format datetime fields
                dt = datetime.fromisoformat(value)
                value = dt.strftime('%Y-%m-%d %H:%M')
            lines.append(f"{label:12} {value}")
    
    return '\n'.join(lines)

