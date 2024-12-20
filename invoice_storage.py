from pathlib import Path
import json
import uuid
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class InvoiceCache:
    def __init__(self):
        # Use absolute path for cache directory
        base_dir = Path(__file__).parent.parent  # Go up one level from the file
        self.cache_dir = base_dir / "invoice_cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.metadata_file = self.cache_dir / "metadata.json"
        logger.info(f"Initialized InvoiceCache with directory: {self.cache_dir}")
        self._load_metadata()

    def _load_metadata(self):
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}
            self._save_metadata()

    def _save_metadata(self):
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def store_invoice(self, file_content, filename, sender):
        """Store invoice and return unique ID"""
        try:
            invoice_id = str(uuid.uuid4())
            logger.info(f"Generated invoice ID: {invoice_id}")
            
            # Store file
            invoice_path = self.cache_dir / f"{invoice_id}_{filename}"
            logger.info(f"Storing invoice at path: {invoice_path}")
            
            with open(invoice_path, 'wb') as f:
                f.write(file_content)
            
            # Store metadata
            self.metadata[invoice_id] = {
                'filename': filename,
                'original_name': filename,
                'timestamp': datetime.now().isoformat(),
                'sender': sender,
                'status': 'pending',
                'path': str(invoice_path)
            }
            logger.info(f"Added metadata for invoice: {self.metadata[invoice_id]}")
            
            self._save_metadata()
            logger.info("Metadata saved successfully")
            
            return invoice_id
        except Exception as e:
            logger.error(f"Failed to store invoice: {e}", exc_info=True)
            raise

    def get_invoice(self, invoice_id):
        """Retrieve invoice by ID"""
        try:
            logger.info(f"Attempting to retrieve invoice with ID: {invoice_id}")
            logger.info(f"Available invoice IDs: {list(self.metadata.keys())}")
            
            if invoice_id not in self.metadata:
                logger.error(f"Invoice ID {invoice_id} not found in metadata")
                return None
            
            invoice_data = self.metadata[invoice_id]
            logger.info(f"Found invoice metadata: {invoice_data}")
            
            invoice_path = Path(invoice_data['path'])
            if not invoice_path.exists():
                logger.error(f"Invoice file not found at path: {invoice_path}")
                return None
            
            with open(invoice_path, 'rb') as f:
                content = f.read()
            
            logger.info(f"Successfully retrieved invoice content for ID: {invoice_id}")
            return {
                'content': content,
                'filename': invoice_data['filename'],
                'metadata': invoice_data
            }
        except Exception as e:
            logger.error(f"Error retrieving invoice: {e}", exc_info=True)
            return None

    def mark_as_processed(self, invoice_id, status='approved'):
        """Mark invoice as processed"""
        if invoice_id in self.metadata:
            self.metadata[invoice_id]['status'] = status
            self._save_metadata()

    def cleanup_old_invoices(self, days=7):
        """Remove processed invoices older than specified days"""
        current_time = datetime.now()
        to_remove = []
        
        for invoice_id, data in self.metadata.items():
            invoice_date = datetime.fromisoformat(data['timestamp'])
            age = (current_time - invoice_date).days
            
            if age > days and data['status'] != 'pending':
                # Remove file
                try:
                    os.remove(data['path'])
                    to_remove.append(invoice_id)
                except Exception as e:
                    logger.error(f"Failed to remove old invoice {invoice_id}: {e}")

        # Update metadata
        for invoice_id in to_remove:
            del self.metadata[invoice_id]
        self._save_metadata()