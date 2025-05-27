"""
Input validation utilities.
"""

import re
import logging
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ValidationError

logger = logging.getLogger("schoolconnect_ai")

class ValidationUtils:
    """Utilities for input validation."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate an email address.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email is valid, False otherwise
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate a URL.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        pattern = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def validate_model(data: Dict[str, Any], model_class: BaseModel) -> Union[BaseModel, List[Dict[str, str]]]:
        """
        Validate data against a Pydantic model.
        
        Args:
            data: Data to validate
            model_class: Pydantic model class
            
        Returns:
            Validated model instance or list of validation errors
        """
        try:
            return model_class(**data)
        except ValidationError as e:
            errors = []
            for error in e.errors():
                errors.append({
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"]
                })
            return errors
    
    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """
        Sanitize input string to prevent injection attacks.
        
        Args:
            input_str: Input string to sanitize
            
        Returns:
            Sanitized string
        """
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>&;]', '', input_str)
        return sanitized
