"""
File utilities for handling file operations.
"""

import os
import logging
import shutil
from typing import Optional

logger = logging.getLogger("schoolconnect_ai")

class FileUtils:
    """Utilities for file operations."""
    
    @staticmethod
    def ensure_directory(directory_path: str) -> bool:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            True if directory exists or was created, False otherwise
        """
        try:
            os.makedirs(directory_path, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating directory {directory_path}: {str(e)}")
            return False
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        Delete a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file was deleted, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return False
    
    @staticmethod
    def copy_file(source_path: str, destination_path: str) -> bool:
        """
        Copy a file.
        
        Args:
            source_path: Path to the source file
            destination_path: Path to the destination file
            
        Returns:
            True if file was copied, False otherwise
        """
        try:
            shutil.copy2(source_path, destination_path)
            return True
        except Exception as e:
            logger.error(f"Error copying file from {source_path} to {destination_path}: {str(e)}")
            return False
    
    @staticmethod
    def move_file(source_path: str, destination_path: str) -> bool:
        """
        Move a file.
        
        Args:
            source_path: Path to the source file
            destination_path: Path to the destination file
            
        Returns:
            True if file was moved, False otherwise
        """
        try:
            shutil.move(source_path, destination_path)
            return True
        except Exception as e:
            logger.error(f"Error moving file from {source_path} to {destination_path}: {str(e)}")
            return False
    
    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """
        Get the extension of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File extension (without the dot)
        """
        return os.path.splitext(file_path)[1][1:]
    
    @staticmethod
    def get_file_size(file_path: str) -> Optional[int]:
        """
        Get the size of a file in bytes.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File size in bytes or None if file doesn't exist
        """
        try:
            if os.path.exists(file_path):
                return os.path.getsize(file_path)
            return None
        except Exception as e:
            logger.error(f"Error getting file size for {file_path}: {str(e)}")
            return None
