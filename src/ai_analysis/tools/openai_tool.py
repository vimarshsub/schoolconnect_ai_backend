"""
OpenAI integration for document analysis.
"""

import os
import logging
import base64
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
        if not os.path.exists(pdf_path):
            error_msg = f"PDF file not found: {pdf_path}"
            logger.error(error_msg)
            return error_msg
        
        try:
            # Convert PDF to images
            base64_images = self.pdf_tool.convert_pdf_to_images(pdf_path)
            if not base64_images:
                error_msg = "Failed to convert PDF to images"
                logger.error(error_msg)
                return error_msg
            
            # Prepare prompt based on analysis type
            if analysis_type == "summarize":
                prompt = "Please provide a comprehensive summary of this document. Include key points, main arguments, and important details."
            elif analysis_type == "extract_action_items":
                prompt = "Please extract all action items, tasks, deadlines, and responsible parties from this document. Format them as a list with clear ownership and timelines if available."
            elif analysis_type == "sentiment":
                prompt = "Please analyze the sentiment and tone of this document. Is it positive, negative, or neutral? What emotions or attitudes are expressed? Provide specific examples from the text."
            elif analysis_type == "custom" and custom_prompt:
                prompt = custom_prompt
            else:
                prompt = "Please analyze this document and provide key insights."
            
            # Prepare messages for OpenAI API
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
            for base64_image in base64_images:
                messages[1]["content"].append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                })
            
            # Call OpenAI API
            logger.info(f"Sending document analysis request to OpenAI for {analysis_type}")
            response = openai.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=4000
            )
            
            # Extract and return the analysis
            analysis = response.choices[0].message.content
            logger.info(f"Received document analysis from OpenAI ({len(analysis)} chars)")
            return analysis
            
        except Exception as e:
            error_msg = f"Error analyzing document: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
