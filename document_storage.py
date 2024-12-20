from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseUpload
import io
import logging
import mimetypes
from datetime import datetime

logger = logging.getLogger(__name__)

class DocumentStorage:
    SCOPES = ['https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = 'service_account.json'
    PARENT_FOLDER_ID = "1ISQ4vECrIclAuo7uH9Bo-8ywy31rbELK"

    def __init__(self):
        self.creds = self._authenticate()
        self.service = build('drive', 'v3', credentials=self.creds)
        # Verify folder access on initialization
        try:
            self.service.files().get(fileId=self.PARENT_FOLDER_ID).execute()
            logger.info(f"Successfully verified access to parent folder: {self.PARENT_FOLDER_ID}")
        except Exception as e:
            logger.error(f"Failed to access parent folder: {e}")
            raise

    def _authenticate(self):
        """Authenticate with Google Drive using service account"""
        try:
            creds = service_account.Credentials.from_service_account_file(
                self.SERVICE_ACCOUNT_FILE, scopes=self.SCOPES
            )
            return creds
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    def store_approved_invoice(self, file_content, filename):
        """Store an approved invoice in Google Drive"""
        try:
            # Ensure we have valid content
            if not file_content:
                raise ValueError("No file content provided")
            
            # Convert file_content to file-like object
            file_stream = io.BytesIO(file_content)
            
            # Try to guess the mime type based on filename
            mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            
            # Create media upload object
            media = MediaIoBaseUpload(
                file_stream,
                mimetype=mime_type,
                resumable=True
            )
            
            # Create a folder structure: YYYY/MM/
            current_date = datetime.now()
            year_folder_name = str(current_date.year)
            month_folder_name = current_date.strftime("%m-%B")
            
            # Create year folder if it doesn't exist
            year_folder = self._get_or_create_folder(year_folder_name, self.PARENT_FOLDER_ID)
            # Create month folder if it doesn't exist
            month_folder = self._get_or_create_folder(month_folder_name, year_folder['id'])
            
            file_metadata = {
                'name': f"APPROVED_{filename}",
                'parents': [month_folder['id']]
            }
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            logger.info(f"Successfully stored file {filename} with ID: {file.get('id')}")
            
            return {
                'file_id': file.get('id'),
                'web_link': file.get('webViewLink')
            }
        except Exception as e:
            logger.error(f"Failed to store file {filename}: {e}", exc_info=True)
            raise

    def _get_or_create_folder(self, folder_name, parent_id):
        """Get or create a folder in Google Drive"""
        try:
            # Check if folder exists
            query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            folders = results.get('files', [])
            
            if folders:
                return folders[0]
            
            # Create folder if it doesn't exist
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            folder = self.service.files().create(body=folder_metadata, fields='id').execute()
            return folder
        except Exception as e:
            logger.error(f"Error in folder operation: {e}", exc_info=True)
            raise