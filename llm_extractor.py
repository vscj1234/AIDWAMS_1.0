import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_key_points_with_gpt(ocr_text, document_type):
    """
    Extract key points from OCR text using GPT
    
    Args:
        ocr_text (str): Text extracted from document
        document_type (str): Type of the document ("invoice" or "general")
    
    Returns:
        str: Summarized key points
    """
    try:
        if document_type == "invoice":
            # Prompt for invoice documents
            structure_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at organizing invoice data. 
                        Extract and structure the following information if available:
                        - Company Name
                        - Invoice Number
                        - Date Information
                        - Customer Details
                        - Items and Services
                        - Payment Terms
                        - Total Amount"""
                    },
                    {
                        "role": "user",
                        "content": f"Structure this invoice text:\n\n{ocr_text}"
                    }
                ],
                temperature=0.3
            )
        else:
            # Prompt for general documents
            structure_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert at summarizing general documents. 
                        Extract and summarize the key points from the following text."""
                    },
                    {
                        "role": "user",
                        "content": f"Summarize this document text:\n\n{ocr_text}"
                    }
                ],
                temperature=0.3
            )
        
        structured_data = structure_response.choices[0].message.content

        # Second prompt to generate natural summary
        summary_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert at summarizing information.
                    Create a concise, natural-sounding summary that includes the main points and any important details."""
                },
                {
                    "role": "user",
                    "content": f"Create a natural summary from this structured data:\n\n{structured_data}"
                }
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        return summary_response.choices[0].message.content.strip()
    
    except Exception as e:
        print(f"LLM Extraction Error: {e}")
        raise

def detect_document_type(text):
    """
    Detect if the document is an invoice or general document using GPT
    
    Args:
        text (str): Extracted text from document
    
    Returns:
        dict: Contains document_type and confidence score
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert at document classification. 
                    Analyze the given text and determine if it's an invoice or a general document.
                    Consider these characteristics of invoices:
                    - Contains billing/payment information
                    - Has invoice number/reference
                    - Lists items/services with prices
                    - Shows total amount
                    - Contains payment terms
                    
                    Respond with a JSON object containing:
                    - document_type: "invoice" or "general"
                    - confidence: number between 0 and 1
                    - reasoning: brief explanation"""
                },
                {
                    "role": "user",
                    "content": f"Classify this document:\n\n{text}"
                }
            ],
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Document Classification Error: {e}")
        raise