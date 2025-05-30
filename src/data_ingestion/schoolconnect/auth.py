"""
Authentication module for SchoolConnect API.
"""

import logging
from typing import Dict, Optional, Tuple

from src.data_ingestion.schoolconnect.client import SchoolConnectClient

logger = logging.getLogger("schoolconnect_ai")

class SchoolConnectAuth:
    """Authentication handler for SchoolConnect API."""
    
    def __init__(self):
        """Initialize the authentication handler."""
        self.client = SchoolConnectClient()
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        Authenticate with SchoolConnect.
        
        Args:
            username: SchoolConnect username
            password: SchoolConnect password
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            success = self.client.login(username, password)
            if success:
                return True, None
            else:
                return False, "Authentication failed. Please check your credentials."
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}", exc_info=True)
            return False, f"Authentication error: {str(e)}"
    
    def get_authenticated_client(self, username: str, password: str) -> Tuple[Optional[SchoolConnectClient], Optional[str]]:
        """
        Get an authenticated SchoolConnect client.
        
        Args:
            username: SchoolConnect username
            password: SchoolConnect password
            
        Returns:
            Tuple of (client, error_message)
        """
        success, error = self.authenticate(username, password)
        if success:
            return self.client, None
        else:
            return None, error
