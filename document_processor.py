import pytesseract
from PIL import Image
import PyPDF2
from docx import Document
import io

def extract_text_from_pdf(file_content):
    """Extract text from PDF file"""
    try:
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"PDF Processing Error: {str(e)}")

def extract_text_from_docx(file_content):
    """Extract text from DOCX file"""
    try:
        docx_file = io.BytesIO(file_content)
        doc = Document(docx_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"DOCX Processing Error: {str(e)}")

def process_document(file_content, filename):
    """
    Process different types of documents and extract text
    
    Args:
        file_content (bytes): Content of the uploaded file
        filename (str): Name of the uploaded file
    
    Returns:
        str: Extracted text from the document
    """
    file_extension = filename.lower().split('.')[-1]
    
    try:
        if file_extension in ['pdf']:
            return extract_text_from_pdf(file_content)
        elif file_extension in ['docx']:
            return extract_text_from_docx(file_content)
        elif file_extension in ['png', 'jpg', 'jpeg']:
            # For images, save to temporary file and use existing OCR
            with open(f"temp_{filename}", "wb") as temp_file:
                temp_file.write(file_content)
            image = Image.open(f"temp_{filename}")
            text = pytesseract.image_to_string(image, lang='eng')
            return text.strip()
        else:
            raise Exception("Unsupported file format")
            
    except Exception as e:
        raise Exception(f"Document Processing Error: {str(e)}")