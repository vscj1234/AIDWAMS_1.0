# approval_manager.py
from email_listener import EmailListener
from approval_analyzer import ApprovalAnalyzer
from document_storage import DocumentStorage
from invoice_storage import InvoiceCache
import json
import logging
import email
import os
from datetime import datetime
from email.header import decode_header

logger = logging.getLogger(__name__)

class ApprovalManager:
    def __init__(self):
        self.email_listener = EmailListener()
        self.analyzer = ApprovalAnalyzer()
        self.storage = DocumentStorage()
        self.invoice_cache = InvoiceCache()  # Add this line
        
    def extract_original_invoice(self, email_data):
        """
        Extract the original invoice from email thread
        Returns dict with content and filename if found, None otherwise
        """
        try:
            # Parse the email message properly from bytes if needed
            email_message = (
                email.message_from_bytes(email_data['body'].encode())
                if isinstance(email_data['body'], str)
                else email.message_from_string(email_data['body'])
            )
            
            # Store all attachments found
            attachments = []
            
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_maintype() == 'application':
                        content_type = part.get_content_type()
                        if content_type in ['application/pdf', 'application/msword', 'image/jpeg', 'image/jpg', 'image/png']:
                            filename = part.get_filename()
                            if filename:
                                # Decode filename if needed
                                filename = decode_header(filename)[0][0]
                                if isinstance(filename, bytes):
                                    filename = filename.decode()
                                
                                content = part.get_payload(decode=True)
                                if content:  # Only append if we actually got content
                                    attachments.append({
                                        'content': content,
                                        'filename': filename
                                    })
                                    logger.info(f"Found attachment: {filename}")
            
            # If we found any attachments, return the first one
            if attachments:
                logger.info(f"Successfully extracted invoice: {attachments[0]['filename']}")
                return attachments[0]
            
            logger.warning("No attachments found in the email")
            return None
                
        except Exception as e:
            logger.error(f"Error extracting original invoice: {e}", exc_info=True)
            return None

    def extract_invoice_id(self, subject):
        """Extract invoice ID from email subject"""
        try:
            if "ID:" in subject:
                return subject.split("ID:")[1].strip()
            return None
        except Exception as e:
            logger.error(f"Error extracting invoice ID: {e}")
            return None

    def process_approval_responses(self):
        """
        Main method to process approval responses with detailed logging
        """
        try:
            self.email_listener.connect()
            processing_summary = {
                'total_processed': 0,
                'approved': 0,
                'rejected': 0,
                'needs_modifications': 0,
                'errors': 0,
                'processed_emails': []
            }
            
            for email_data in self.email_listener.check_approval_responses():
                try:
                    # Extract invoice ID from subject
                    invoice_id = self.extract_invoice_id(email_data['subject'])
                    if not invoice_id:
                        logger.error("No invoice ID found in email subject")
                        processing_summary['errors'] += 1
                        continue

                    # Get original invoice from cache
                    invoice_data = self.invoice_cache.get_invoice(invoice_id)
                    if not invoice_data:
                        logger.error(f"Original invoice not found for ID: {invoice_id}")
                        processing_summary['errors'] += 1
                        continue

                    logger.info(f"""
                    ==========================================================
                    Starting to process email:
                    From: {email_data['sender']}
                    Subject: {email_data['subject']}
                    ==========================================================
                    """)
                    
                    # Analyze response with LLM
                    logger.info("Analyzing email content with LLM...")
                    analysis = self.analyzer.analyze_response(email_data['body'])
                    
                    # Only parse as JSON if it's a string
                    if isinstance(analysis, str):
                        analysis = json.loads(analysis)
                    
                    logger.info(f"""
                    LLM Analysis Result:
                    Status: {analysis['status']}
                    Confidence: {analysis['confidence']}
                    Reason: {analysis.get('reason', 'Not provided')}
                    """)
                    
                    # Process based on analysis
                    if analysis['status'] == 'approved' and analysis['confidence'] > 0.8:
                        logger.info("Invoice APPROVED - Processing approval...")
                        try:
                            # Use the cached invoice instead of extracting from email
                            logger.info(f"Processing cached invoice: {invoice_data['filename']}")
                            storage_result = self.storage.store_approved_invoice(
                                invoice_data['content'],
                                invoice_data['filename']
                            )
                            logger.info(f"Invoice stored successfully: {storage_result['web_link']}")
                            
                            # Handle successful storage with invoice_id
                            self.handle_successful_approval(storage_result, email_data, invoice_id)
                            processing_summary['approved'] += 1
                            
                        except Exception as e:
                            logger.error(f"Failed to store approved invoice: {e}", exc_info=True)
                            processing_summary['errors'] += 1
                    
                    elif analysis['status'] == 'rejected':
                        logger.info("Invoice REJECTED - Processing rejection...")
                        self.handle_rejection(analysis, email_data)
                        processing_summary['rejected'] += 1
                    
                    elif analysis['status'] == 'needs_modifications':
                        logger.info("Invoice needs MODIFICATIONS - Processing request...")
                        self.handle_modification_request(analysis, email_data)
                        processing_summary['needs_modifications'] += 1
                    
                    # Mark email as processed
                    self.email_listener.imap.store(email_data['message_id'], '+FLAGS', '\\Seen')
                    processing_summary['total_processed'] += 1
                    
                    # Add to processed emails list
                    processing_summary['processed_emails'].append({
                        'timestamp': datetime.now().isoformat(),
                        'sender': email_data['sender'],
                        'subject': email_data['subject'],
                        'status': analysis['status'],
                        'confidence': analysis['confidence']
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing individual email: {e}")
                    processing_summary['errors'] += 1
                    continue
            
            # Log final summary
            logger.info(f"""
            ==========================================================
            Email Processing Summary:
            Total Processed: {processing_summary['total_processed']}
            Approved: {processing_summary['approved']}
            Rejected: {processing_summary['rejected']}
            Needs Modifications: {processing_summary['needs_modifications']}
            Errors: {processing_summary['errors']}
            ==========================================================
            """)
            
            return processing_summary
                
        except Exception as e:
            logger.error(f"Error in approval process: {e}")
            raise
        finally:
            self.email_listener.imap.logout()

    def handle_successful_approval(self, storage_result, email_data, invoice_id):
        """Handle additional tasks after successful approval"""
        try:
            # Log the approval
            approval_log = {
                'timestamp': datetime.now().isoformat(),
                'invoice_id': invoice_id,
                'approver': email_data['sender'],
                'file_id': storage_result['file_id'],
                'file_link': storage_result['web_link'],
                'status': 'approved'
            }
            
            # Here you might want to:
            # 1. Store approval_log in database
            # 2. Send confirmation emails
            # 3. Update other systems
            
            logger.info(f"Approval processed successfully: {approval_log}")
            
        except Exception as e:
            logger.error(f"Error in handling successful approval: {e}")

    def handle_rejection(self, analysis, email_data):
        """Handle rejected invoices"""
        try:
            rejection_log = {
                'timestamp': datetime.now().isoformat(),
                'approver': email_data['sender'],
                'reason': analysis['reason'],
                'status': 'rejected'
            }
            
            # Here you might want to:
            # 1. Notify relevant parties
            # 2. Update status in your system
            # 3. Archive the rejected invoice
            
            logger.info(f"Invoice rejected: {rejection_log}")
            
        except Exception as e:
            logger.error(f"Error handling rejection: {e}")

    def handle_modification_request(self, analysis, email_data):
        """Handle modification requests"""
        try:
            modification_log = {
                'timestamp': datetime.now().isoformat(),
                'approver': email_data['sender'],
                'requested_changes': analysis['reason'],
                'status': 'needs_modifications'
            }
            
            # Here you might want to:
            # 1. Create modification request ticket
            # 2. Notify relevant parties
            # 3. Update status in your system
            
            logger.info(f"Modification requested: {modification_log}")
            
        except Exception as e:
            logger.error(f"Error handling modification request: {e}")

            