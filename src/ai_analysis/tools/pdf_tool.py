"""
PDF to image conversion tool for document analysis.
"""

import os
import base64
import logging
from typing import List, Optional
from pdf2image import convert_from_path

from src.core.config import get_settings

logger = logging.getLogger("schoolconnect_ai")

class PDFTool:
    """Tool for converting PDF documents to images for analysis."""
    
    def __init__(self):
        """Initialize the PDF tool."""
        self.settings = get_settings()
    
    def convert_pdf_to_images(self, pdf_path: str, max_pages: int = 5) -> List[str]:
        """
        Convert PDF file to a list of base64-encoded images.
        
        Args:
            pdf_path: Path to the PDF file
            max_pages: Maximum number of pages to convert
            
        Returns:
            List of base64-encoded image strings
        """
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return []
        
        try:
            logger.info(f"Converting PDF to images: {pdf_path}")
            
            # Convert PDF to images
            images = convert_from_path(
                pdf_path,
                dpi=200,
                first_page=1,
                last_page=max_pages
            )
            
            logger.info(f"Converted {len(images)} pages from PDF")
            
            # Convert images to base64
            base64_images = []
            for i, image in enumerate(images):
                img_path = f"{os.path.splitext(pdf_path)[0]}_page_{i+1}.png"
                image.save(img_path, "PNG")
                
                with open(img_path, "rb") as img_file:
                    encoded_string = base64.b64encode(img_file.read()).decode("utf-8")
                    base64_images.append(encoded_string)
                
                # Clean up temporary image file
                os.remove(img_path)
            
            return base64_images
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {str(e)}", exc_info=True)
            return []
