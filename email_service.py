import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import json
from invoice_storage import InvoiceCache
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"  # or your SMTP server
        self.smtp_port = 587  # Standard TLS port
        self.sender_email = "khandelwal.sarvesh1990@gmail.com"  # Replace with your email
        self.password = "upqw bivh lfak uwjt"  # Replace with your app password
        self._load_email_list()
        # Add invoice cache initialization
        self.invoice_cache = InvoiceCache()  # Add this line

    def _load_email_list(self):
        """Load email addresses from JSON file"""
        try:
            current_dir = Path(__file__).parent
            with open(current_dir / 'email_list.json', 'r') as f:
                self.email_list = json.load(f)
        except Exception as e:
            logger.error(f"Error loading email list: {e}")
            self.email_list = {}

    def get_approvers_list(self):
        """Return list of available approvers"""
        return list(self.email_list.keys())

    def send_invoice_email(self, approver, extraction_result, file_content, filename):
        """Send invoice email using SMTP"""
        try:
            # Add debug logging before storing
            logger.info(f"Attempting to store invoice in cache: {filename}")
            
            # Store invoice in cache first
            invoice_id = self.invoice_cache.store_invoice(file_content, filename, approver)
            logger.info(f"Successfully stored invoice in cache with ID: {invoice_id}")
            
            # Create email with invoice ID in subject
            subject = f"Invoice Approval Request - {filename} - ID:{invoice_id}"
            
            if approver not in self.email_list:
                raise ValueError(f"Approver {approver} not found in email list")

            recipient_email = self.email_list[approver]

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject

            # Create email body with extraction results
            body = "Please review the following invoice details:\n\n"
            
            # Handle different types of extraction_result
            if isinstance(extraction_result, dict):
                for key, value in extraction_result.items():
                    body += f"{key}: {value}\n"
            else:
                # If it's a string or any other type, convert to string
                body += str(extraction_result)
                
            body += "\nPlease review the attached invoice."

            msg.attach(MIMEText(body, 'plain'))

            # Attach the invoice file
            attachment = MIMEApplication(file_content)
            attachment.add_header(
                'Content-Disposition', 
                'attachment', 
                filename=filename
            )
            msg.attach(attachment)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {recipient_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise