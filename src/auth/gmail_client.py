"""
# src/auth/gmail_client.py
# Gmail API client wrapper for email operations
"""

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from typing import List, Dict, Any
import base64
import email
import logging

logger = logging.getLogger(__name__)

class GmailClient:
    def __init__(self, credentials: Credentials):
        """Initialize Gmail API client with credentials."""
        logger.info("Initializing Gmail client")
        self.service = build('gmail', 'v1', credentials=credentials)
        logger.debug("Gmail client initialized successfully")

    def search_messages(self, query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Search for messages matching the query."""
        try:
            logger.debug(f"Searching messages with query: {query}")
            result = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = result.get('messages', [])
            logger.info(f"Found {len(messages)} messages matching query")
            return messages
        except Exception as e:
            logger.error(f"Error searching messages: {e}", exc_info=True)
            return []

    def get_message(self, message_id: str) -> Dict[str, Any]:
        """Get full message details by ID."""
        try:
            logger.debug(f"Fetching message details for ID: {message_id}")
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            logger.debug(f"Successfully fetched message {message_id}")
            return message
        except Exception as e:
            logger.error(f"Error getting message {message_id}: {e}", exc_info=True)
            return {}

    def parse_message_content(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse message content into a structured format."""
        try:
            logger.debug("Parsing message content")
            headers = {
                header['name'].lower(): header['value']
                for header in message['payload']['headers']
            }

            parts = []
            if 'parts' in message['payload']:
                parts = message['payload']['parts']
                logger.debug(f"Message has {len(parts)} parts")
            else:
                parts = [message['payload']]
                logger.debug("Message has single part")

            content = {
                'subject': headers.get('subject', ''),
                'from': headers.get('from', ''),
                'date': headers.get('date', ''),
                'body': self._get_message_body(parts)
            }

            logger.debug(f"Successfully parsed message with subject: {content['subject']}")
            return content
        except Exception as e:
            logger.error("Error parsing message content", exc_info=True)
            return {
                'subject': '',
                'from': '',
                'date': '',
                'body': ''
            }

    def _get_message_body(self, parts: List[Dict[str, Any]]) -> str:
        """Extract message body from message parts."""
        text_content = []
        
        try:
            for part in parts:
                if part.get('mimeType') == 'text/plain':
                    if 'data' in part['body']:
                        text = base64.urlsafe_b64decode(
                            part['body']['data'].encode('ASCII')
                        ).decode('utf-8')
                        text_content.append(text)
                        logger.debug("Extracted text/plain content")
                elif part.get('parts'):
                    logger.debug("Processing nested message parts")
                    text_content.append(self._get_message_body(part['parts']))

            return '\n'.join(text_content)
        except Exception as e:
            logger.error("Error extracting message body", exc_info=True)
            return "" 