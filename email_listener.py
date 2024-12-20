# email_listener.py
from imaplib import IMAP4_SSL
import email
from email.header import decode_header
import logging
import os
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailListener:
    def __init__(self):
        self.email_address = "khandelwal.sarvesh1990@gmail.com"
        self.password = "upqw bivh lfak uwjt"
        self.imap_server = "imap.gmail.com"
        self.last_processed_emails = []  # Store recently processed emails

    def connect(self):
        logger.info("Connecting to email server...")
        self.imap = IMAP4_SSL(self.imap_server)
        self.imap.login(self.email_address, self.password)
        logger.info("Successfully connected to email server")

    def check_approval_responses(self):
        try:
            self.imap.select('INBOX')
            logger.info("Searching for unread approval response emails...")
            
            # Search for unread emails with "Re: Invoice Approval Request" in subject
            _, message_numbers = self.imap.search(None, 
                '(UNSEEN SUBJECT "Re: Invoice Approval Request")')
            
            if not message_numbers[0]:
                logger.info("No new approval response emails found")
                return []

            messages_found = message_numbers[0].split()
            logger.info(f"Found {len(messages_found)} new approval response emails")

            for num in messages_found:
                _, msg_data = self.imap.fetch(num, '(RFC822)')
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                subject = decode_header(email_message["subject"])[0][0]
                sender = email_message.get("from")
                
                # Get email content
                body = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                else:
                    body = email_message.get_payload(decode=True).decode()

                logger.info(f"""
                Processing email:
                From: {sender}
                Subject: {subject}
                Message ID: {num}
                Body Preview: {body[:100]}...
                """)

                email_data = {
                    "subject": subject,
                    "sender": sender,
                    "body": body,
                    "message_id": num
                }

                self.last_processed_emails.append({
                    "timestamp": datetime.now().isoformat(),
                    "sender": sender,
                    "subject": subject
                })

                yield email_data

        except Exception as e:
            logger.error(f"Error checking emails: {e}")
            raise

    def get_processing_history(self):
        """Return the last processed emails"""
        return self.last_processed_emails