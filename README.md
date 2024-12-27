=> The process begins when a user uploads a document through the FastAPI endpoint in `main.py`, which triggers the document processing chain. 

=> The uploaded file is first processed by `document_processor.py`, which handles different file formats (PDF, DOCX, images) and extracts text content, utilizing `ocr_processor.py` for image-based documents using Tesseract OCR. 

=> The extracted text is then analyzed by `llm_extractor.py`, it uses GPT to detect the document type and extract key information. 

=> The document and its metadata are stored in a local cache using `invoice_storage.py`, and generates a unique ID for tracking. 

=> The `email_service.py` then creates and sends an approval request email to the designated approver, including the document as an attachment and the unique ID in the subject. 

=> A background thread in `main.py` continuously runs the approval checking process, where `approval_manager.py` works with `email_listener.py` to monitor for approval responses. 


=> When a response is received, `approval_analyzer.py` uses GPT to analyze the response content and determine the approval status (approved/rejected/needs modifications). 

=> For approved documents, `document_storage.py` handles the final storage in Google Drive with an organized folder structure (Year/Month), while rejected or modification-needed documents trigger appropriate logging and status updates. 

=> Throughout this process, comprehensive error handling and logging are maintained, and the `InvoiceCache` system ensures proper tracking and retrieval of documents during the approval workflow.
