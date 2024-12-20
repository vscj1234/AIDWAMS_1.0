import pytesseract
from PIL import Image

def process_image_with_tesseract(image_path):
    """
    Process image using Tesseract OCR and return extracted text
    
    Args:
        image_path (str): Path to the image file
    
    Returns:
        str: Extracted text from the image
    """
    try:
        # Open the image
        image = Image.open(image_path)
        
        # Use Tesseract to do OCR on the image
        text = pytesseract.image_to_string(image, lang='eng')
        
        return text.strip()
    
    except Exception as e:
        print(f"OCR Processing Error: {e}")
        raise