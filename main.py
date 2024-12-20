import os
from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from llm_extractor import extract_key_points_with_gpt, detect_document_type
from document_processor import process_document
from email_service import EmailService
import logging
from pathlib import Path
import json
from approval_manager import ApprovalManager
import asyncio
import threading
import time
from invoice_storage import InvoiceCache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize shared components
invoice_cache = InvoiceCache()
email_service = EmailService()
approval_manager = ApprovalManager()

# Update the instances to share the same invoice cache
email_service.invoice_cache = invoice_cache
approval_manager.invoice_cache = invoice_cache

# Create a function to run the approval checker in the background
def run_approval_checker():
    while True:
        try:
            approval_manager.process_approval_responses()
            # Check every 5 minutes
            time.sleep(300)
        except Exception as e:
            logger.error(f"Error in approval checker: {e}")
            time.sleep(60)  # Wait a minute before retrying

# Start the approval checker in a separate thread
@app.on_event("startup")
async def startup_event():
    thread = threading.Thread(target=run_approval_checker, daemon=True)
    thread.start()

@app.get("/")
async def serve_index(request: Request):
    """
    Serve the main index page
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/approvers/")
async def get_approvers():
    """Get list of available approvers"""
    try:
        logger.info("Fetching approvers list...")
        approvers = email_service.get_approvers_list()
        logger.info(f"Retrieved approvers: {approvers}")
        
        if not approvers:
            logger.warning("No approvers found in the list")
        
        return {"approvers": approvers}
    except Exception as e:
        logger.error(f"Error getting approvers: {e}")
        return {"approvers": [], "error": str(e)}

@app.post("/upload-invoice/")
async def upload_invoice(
    file: UploadFile = File(...),
    approver: str = Form(None)
):
    """
    Endpoint to upload invoice file and send for approval
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Process document based on file type
        extracted_text = process_document(file_content, file.filename)
        
        # Detect document type
        doc_classification = json.loads(detect_document_type(extracted_text))
        
        # Extract key points using GPT
        extraction_result = extract_key_points_with_gpt(extracted_text, doc_classification['document_type'])
        
        # Automatically set approver based on document type
        if doc_classification['document_type'] == 'invoice' and doc_classification['confidence'] > 0.8:
            approver = "Finance"
        elif doc_classification['document_type'] == 'general':
            approver = "Normal"
        
        # Send email if approver is set (either manually or automatically)
        email_sent = False
        if approver:
            try:
                email_service.send_invoice_email(
                    approver,
                    extraction_result,
                    file_content,
                    file.filename
                )
                email_sent = True
            except Exception as e:
                logger.error(f"Email sending failed: {e}")
        
        return {
            "status": "success",
            "document_type": doc_classification,
            "extracted_text": extracted_text,
            "key_points": extraction_result,
            "email_sent": email_sent,
            "approver": approver
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/test-email-list/")
async def test_email_list():
    """Test endpoint to verify email list loading"""
    try:
        # Get the current directory
        current_dir = Path(__file__).parent
        email_list_path = current_dir / 'email_list.json'
        
        # Check if file exists
        if not email_list_path.exists():
            return {
                "status": "error",
                "message": f"email_list.json not found at {email_list_path}"
            }
            
        # Try to read the file
        with open(email_list_path, 'r') as f:
            content = json.load(f)
            
        return {
            "status": "success",
            "file_path": str(email_list_path),
            "content": content,
            "approvers": list(content.keys())
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/check-email-processing/")
async def check_email_processing():
    """
    Get the status of email processing
    """
    try:
        # Get processing history from the approval manager
        processing_summary = approval_manager.process_approval_responses()
        
        return {
            "status": "success",
            "processing_summary": processing_summary
        }
    except Exception as e:
        logger.error(f"Error checking email processing: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

    ##uvicorn main:app --reload 
    