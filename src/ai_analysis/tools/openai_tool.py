"""
OpenAI integration for document analysis.
"""

import os
import logging
import base64
import time
from typing import List, Optional, Dict, Any
import openai

from src.core.config import get_settings
from src.ai_analysis.tools.pdf_tool import PDFTool

logger = logging.getLogger("schoolconnect_ai")

class OpenAIDocumentAnalysisTool:
    """Tool for analyzing documents using OpenAI's vision capabilities."""
    
    def __init__(self):
        """Initialize the OpenAI document analysis tool."""
        settings = get_settings()
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.pdf_tool = PDFTool()
        
        # Set OpenAI API key
        openai.api_key = self.api_key
        logger.info(f"OpenAIDocumentAnalysisTool initialized with model: {self.model}")
    
    def analyze_document(self, pdf_path: str, analysis_type: str = "summarize", custom_prompt: Optional[str] = None) -> str:
        """
        Analyze a PDF document using OpenAI's vision capabilities.
        
        Args:
            pdf_path: Path to the PDF file
            analysis_type: Type of analysis to perform (summarize, extract_action_items, sentiment, custom)
            custom_prompt: Custom prompt for analysis (used when analysis_type is 'custom')
            
        Returns:
            Analysis result or error message
        """
        logger.info(f"Starting document analysis for PDF: {pdf_path}, analysis type: {analysis_type}")
        
        # Check if PDF file exists
        if not os.path.exists(pdf_path):
            error_msg = f"PDF file not found: {pdf_path}"
            logger.error(error_msg)
            return error_msg
        
        logger.info(f"PDF file exists: {pdf_path}, size: {os.path.getsize(pdf_path)} bytes")
        
        try:
            # Convert PDF to images
            logger.info(f"Starting PDF to image conversion for: {pdf_path}")
            start_time = time.time()
            base64_images = self.pdf_tool.convert_pdf_to_images(pdf_path)
            conversion_time = time.time() - start_time
            
            if not base64_images:
                error_msg = "Failed to convert PDF to images"
                logger.error(error_msg)
                return error_msg
            
            logger.info(f"Successfully converted PDF to {len(base64_images)} images in {conversion_time:.2f} seconds")
            logger.info(f"First image size (base64): {len(base64_images[0])} chars")
            
            # Prepare prompt based on analysis type
            logger.info(f"Preparing prompt for analysis type: {analysis_type}")
            if analysis_type == "summarize":
                prompt = "Please provide a comprehensive summary of this document. Include key points, main arguments, and important details."
            elif analysis_type == "extract_action_items":
                prompt = "Please extract all action items, tasks, deadlines, and responsible parties from this document. Format them as a list with clear ownership and timelines if available."
            elif analysis_type == "sentiment":
                prompt = "Please analyze the sentiment and tone of this document. Is it positive, negative, or neutral? What emotions or attitudes are expressed? Provide specific examples from the text."
            elif analysis_type == "custom" and custom_prompt:
                prompt = custom_prompt
                logger.info(f"Using custom prompt: {prompt[:100]}...")
            else:
                prompt = "Please analyze this document and provide key insights."
            
            # Prepare messages for OpenAI API
            logger.info("Preparing messages for OpenAI API")
            messages = [
                {
                    "role": "system",
                    "content": "You are a document analysis assistant. You can see images of document pages and provide detailed analysis based on their content."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
            
            # Add images to the user message
            for i, base64_image in enumerate(base64_images):
                logger.info(f"Adding image {i+1}/{len(base64_images)} to message")
                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                })
            
            # Call OpenAI API
            logger.info(f"Sending document analysis request to OpenAI for {analysis_type}")
            logger.info(f"Request details: model={self.model}, images={len(base64_images)}, max_tokens=4000")
            
            start_time = time.time()
            try:
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=4000,
                    timeout=120  # Increased timeout for larger documents
                )
                api_time = time.time() - start_time
                logger.info(f"OpenAI API call successful in {api_time:.2f} seconds")
                
                # Extract and return the analysis
                analysis = response.choices[0].message.content
                logger.info(f"Received document analysis from OpenAI ({len(analysis)} chars)")
                logger.info(f"Analysis preview: {analysis[:100]}...")
                return analysis
                
            except openai.RateLimitError as e:
                error_msg = f"Rate limit exceeded when analyzing document: {str(e)}"
                logger.error(error_msg)
                return f"It seems that there is a temporary rate limit issue with analyzing the document. You can try again in a few moments. Error details: {str(e)}"
                
            except openai.APITimeoutError as e:
                error_msg = f"Timeout when analyzing document: {str(e)}"
                logger.error(error_msg)
                return f"The document analysis request timed out. This might be due to the document size or complexity. You can try again or use a smaller document. Error details: {str(e)}"
                
            except openai.APIError as e:
                error_msg = f"OpenAI API error when analyzing document: {str(e)}"
                logger.error(error_msg)
                return f"There was an error with the OpenAI service when analyzing the document. You can try again in a few moments. Error details: {str(e)}"
            
        except Exception as e:
            error_msg = f"Error analyzing document: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
