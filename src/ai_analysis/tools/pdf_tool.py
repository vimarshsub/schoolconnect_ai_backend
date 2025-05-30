"""
PDF to image conversion tool for document analysis.
"""

import os
import base64
import logging
import time
from typing import List, Optional
from pdf2image import convert_from_path

from src.core.config import get_settings

logger = logging.getLogger("schoolconnect_ai")

class PDFTool:
    """Tool for converting PDF documents to images for analysis."""
    
    def __init__(self):
        """Initialize the PDF tool."""
        self.settings = get_settings()
        logger.info("PDFTool initialized")
    
    def convert_pdf_to_images(self, pdf_path: str, max_pages: int = 5) -> List[str]:
        """
        Convert PDF file to a list of base64-encoded images.
        
        Args:
            pdf_path: Path to the PDF file
            max_pages: Maximum number of pages to convert
            
        Returns:
            List of base64-encoded image strings
        """
        logger.info(f"Starting PDF to image conversion: {pdf_path}, max_pages={max_pages}")
        
        # Check if file exists
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found: {pdf_path}")
            return []
        
        # Check file size
        file_size = os.path.getsize(pdf_path)
        logger.info(f"PDF file size: {file_size} bytes")
        
        try:
            # Get PDF info
            try:
                from pdf2image import pdfinfo_from_path
                pdf_info = pdfinfo_from_path(pdf_path)
                total_pages = pdf_info["Pages"]
                logger.info(f"PDF info: {total_pages} total pages, converting up to {max_pages} pages")
            except Exception as e:
                logger.warning(f"Could not get PDF info: {str(e)}")
                total_pages = "unknown"
            
            # Convert PDF to images
            start_time = time.time()
            logger.info(f"Starting conversion with pdf2image, dpi=200")
            
            images = convert_from_path(
                pdf_path,
                dpi=200,
                first_page=1,
                last_page=max_pages
            )
            
            conversion_time = time.time() - start_time
            logger.info(f"Converted {len(images)}/{total_pages} pages from PDF in {conversion_time:.2f} seconds")
            
            if not images:
                logger.error(f"No images were generated from PDF: {pdf_path}")
                return []
            
            # Convert images to base64
            base64_images = []
            for i, image in enumerate(images):
                logger.info(f"Processing page {i+1}: saving temporary image")
                img_path = f"{os.path.splitext(pdf_path)[0]}_page_{i+1}.png"
                image.save(img_path, "PNG")
                
                logger.info(f"Converting image to base64: {img_path}")
                with open(img_path, "rb") as img_file:
                    encoded_string = base64.b64encode(img_file.read()).decode("utf-8")
                    base64_images.append(encoded_string)
                    logger.info(f"Base64 conversion complete for page {i+1}, size: {len(encoded_string)} chars")
                
                # Clean up temporary image file
                logger.info(f"Removing temporary image file: {img_path}")
                os.remove(img_path)
            
            logger.info(f"PDF to image conversion complete: {len(base64_images)} images generated")
            return base64_images
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {str(e)}", exc_info=True)
            # Add more detailed error information
            if "poppler" in str(e).lower():
                logger.error("This error may be related to missing poppler-utils. Please ensure it's installed.")
            elif "permission" in str(e).lower():
                logger.error("This error may be related to file permissions. Please check file access rights.")
            return []
