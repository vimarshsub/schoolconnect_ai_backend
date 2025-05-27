"""
Data models for SchoolConnect API.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SchoolConnectUser(BaseModel):
    """SchoolConnect user model."""
    
    id: str
    dbId: str
    permittedName: Optional[str] = None
    avatarUrl: Optional[str] = None


class SchoolConnectDocument(BaseModel):
    """SchoolConnect document model."""
    
    id: str
    fileFilename: str
    fileUrl: str
    contentType: str


class SchoolConnectAnnouncement(BaseModel):
    """SchoolConnect announcement model."""
    
    id: str
    dbId: str
    title: str
    message: str
    createdAt: str
    user: SchoolConnectUser
    documentsCount: int = 0
    documents: Optional[List[SchoolConnectDocument]] = None


class AirtableAttachment(BaseModel):
    """Airtable attachment model."""
    
    url: str
    filename: str


class AirtableRecord(BaseModel):
    """Airtable record model for announcements."""
    
    AnnouncementId: str
    Title: str
    Description: str
    SentByUser: str
    DocumentsCount: int = 0
    SentTime: str
    Attachments: Optional[List[AirtableAttachment]] = None
