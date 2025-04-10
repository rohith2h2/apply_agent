"""
Application Data Collector
=========================
This module records and processes data from job applications filled by the user.
"""

import os
import json
import uuid
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class ApplicationField:
    """Represents a field in a job application form."""
    
    def __init__(self, 
                 field_id: str,
                 name: str,
                 type: str,
                 value: Any,
                 options: Optional[List[str]] = None,
                 required: bool = False,
                 placeholder: Optional[str] = None,
                 section: Optional[str] = None):
        """
        Initialize an application field.
        
        Args:
            field_id (str): Unique identifier for the field
            name (str): Display name of the field
            type (str): Field type (text, textarea, select, checkbox, etc.)
            value (Any): The value entered by the user
            options (List[str], optional): Available options for select/radio types
            required (bool): Whether the field is required
            placeholder (str, optional): Placeholder text
            section (str, optional): The section this field belongs to
        """
        self.field_id = field_id
        self.name = name
        self.type = type
        self.value = value
        self.options = options
        self.required = required
        self.placeholder = placeholder
        self.section = section
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the field to a dictionary."""
        return {
            "field_id": self.field_id,
            "name": self.name,
            "type": self.type,
            "value": self.value,
            "options": self.options,
            "required": self.required,
            "placeholder": self.placeholder,
            "section": self.section
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplicationField':
        """Create a field from a dictionary."""
        return cls(
            field_id=data["field_id"],
            name=data["name"],
            type=data["type"],
            value=data["value"],
            options=data.get("options"),
            required=data.get("required", False),
            placeholder=data.get("placeholder"),
            section=data.get("section")
        )

class ApplicationData:
    """Represents a complete job application."""
    
    def __init__(self,
                 application_id: Optional[str] = None,
                 company: str = "",
                 job_title: str = "",
                 job_description: str = "",
                 application_url: str = "",
                 fields: Optional[List[ApplicationField]] = None,
                 status: str = "observed",
                 notes: Optional[str] = None,
                 tags: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize application data.
        
        Args:
            application_id (str, optional): Unique ID for the application
            company (str): Company name
            job_title (str): Job title
            job_description (str): Job description
            application_url (str): URL of the application form
            fields (List[ApplicationField], optional): Form fields with values
            status (str): Application status
            notes (str, optional): Additional notes
            tags (List[str], optional): Tags for categorization
            metadata (Dict[str, Any], optional): Additional metadata
        """
        self.application_id = application_id or str(uuid.uuid4())
        self.company = company
        self.job_title = job_title
        self.job_description = job_description
        self.application_url = application_url
        self.fields = fields or []
        self.status = status
        self.notes = notes
        self.tags = tags or []
        self.metadata = metadata or {}
        
        # Add timestamps if not in metadata
        if "created_at" not in self.metadata:
            self.metadata["created_at"] = datetime.now().isoformat()
        self.metadata["updated_at"] = datetime.now().isoformat()
    
    def add_field(self, field: ApplicationField) -> None:
        """Add a field to the application data."""
        self.fields.append(field)
        self.metadata["updated_at"] = datetime.now().isoformat()
    
    def get_field_by_id(self, field_id: str) -> Optional[ApplicationField]:
        """Get a field by its ID."""
        for field in self.fields:
            if field.field_id == field_id:
                return field
        return None
    
    def get_fields_by_section(self, section: str) -> List[ApplicationField]:
        """Get all fields in a specific section."""
        return [field for field in self.fields if field.section == section]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the application data to a dictionary."""
        return {
            "application_id": self.application_id,
            "company": self.company,
            "job_title": self.job_title,
            "job_description": self.job_description,
            "application_url": self.application_url,
            "fields": [field.to_dict() for field in self.fields],
            "status": self.status,
            "notes": self.notes,
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplicationData':
        """Create an application data object from a dictionary."""
        fields = [ApplicationField.from_dict(field_data) for field_data in data.get("fields", [])]
        return cls(
            application_id=data.get("application_id"),
            company=data.get("company", ""),
            job_title=data.get("job_title", ""),
            job_description=data.get("job_description", ""),
            application_url=data.get("application_url", ""),
            fields=fields,
            status=data.get("status", "observed"),
            notes=data.get("notes"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )

class ApplicationCollector:
    """Manages the collection and storage of application data."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the application collector.
        
        Args:
            data_dir (str, optional): Directory to store application data
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            base_dir = Path(__file__).parent.parent.parent
            self.data_dir = base_dir / "data" / "applications"
        
        # Create the data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.current_application: Optional[ApplicationData] = None
        self.recording: bool = False
        
        logger.info(f"Application data will be stored in {self.data_dir}")
    
    def start_recording(self, 
                        company: str,
                        job_title: str,
                        job_description: str = "",
                        application_url: str = "",
                        tags: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Start recording a new application.
        
        Args:
            company (str): Company name
            job_title (str): Job title
            job_description (str): Job description
            application_url (str): URL of the application form
            tags (List[str], optional): Tags for categorization
            
        Returns:
            Tuple[bool, str]: Success status and message or application ID
        """
        if self.recording:
            return False, "Already recording an application. Please finish or cancel it first."
        
        try:
            self.current_application = ApplicationData(
                company=company,
                job_title=job_title,
                job_description=job_description,
                application_url=application_url,
                tags=tags or []
            )
            self.recording = True
            
            logger.info(f"Started recording application for {company} - {job_title}")
            return True, self.current_application.application_id
        except Exception as e:
            logger.error(f"Failed to start recording: {e}", exc_info=True)
            return False, f"Failed to start recording: {str(e)}"
    
    def record_field(self,
                    name: str,
                    value: Any,
                    field_type: str = "text",
                    options: Optional[List[str]] = None,
                    required: bool = False,
                    placeholder: Optional[str] = None,
                    section: Optional[str] = None) -> Tuple[bool, str]:
        """
        Record a field in the current application.
        
        Args:
            name (str): Field name
            value (Any): Field value
            field_type (str): Field type
            options (List[str], optional): Available options
            required (bool): Whether the field is required
            placeholder (str, optional): Placeholder text
            section (str, optional): Section name
            
        Returns:
            Tuple[bool, str]: Success status and message or field ID
        """
        if not self.recording or not self.current_application:
            return False, "Not currently recording an application."
        
        try:
            field_id = str(uuid.uuid4())
            field = ApplicationField(
                field_id=field_id,
                name=name,
                type=field_type,
                value=value,
                options=options,
                required=required,
                placeholder=placeholder,
                section=section
            )
            self.current_application.add_field(field)
            
            logger.debug(f"Recorded field: {name} = {value}")
            return True, field_id
        except Exception as e:
            logger.error(f"Failed to record field: {e}", exc_info=True)
            return False, f"Failed to record field: {str(e)}"
    
    def finish_recording(self, notes: Optional[str] = None) -> Tuple[bool, str]:
        """
        Finish recording the current application and save it.
        
        Args:
            notes (str, optional): Additional notes
            
        Returns:
            Tuple[bool, str]: Success status and message or application ID
        """
        if not self.recording or not self.current_application:
            return False, "Not currently recording an application."
        
        try:
            # Add notes if provided
            if notes:
                self.current_application.notes = notes
            
            # Save the application data
            self._save_application(self.current_application)
            
            app_id = self.current_application.application_id
            self.current_application = None
            self.recording = False
            
            logger.info(f"Finished recording application with ID: {app_id}")
            return True, app_id
        except Exception as e:
            logger.error(f"Failed to finish recording: {e}", exc_info=True)
            return False, f"Failed to finish recording: {str(e)}"
    
    def cancel_recording(self) -> bool:
        """
        Cancel the current recording without saving.
        
        Returns:
            bool: Success status
        """
        if not self.recording:
            return False
        
        self.current_application = None
        self.recording = False
        
        logger.info("Cancelled recording application")
        return True
    
    def _save_application(self, application: ApplicationData) -> None:
        """
        Save application data to a file.
        
        Args:
            application (ApplicationData): The application data to save
        """
        file_path = self.data_dir / f"{application.application_id}.json"
        
        with open(file_path, 'w') as f:
            json.dump(application.to_dict(), f, indent=4)
        
        logger.info(f"Saved application data to {file_path}")
    
    def get_application(self, application_id: str) -> Optional[ApplicationData]:
        """
        Get an application by its ID.
        
        Args:
            application_id (str): Application ID
            
        Returns:
            Optional[ApplicationData]: The application data or None if not found
        """
        file_path = self.data_dir / f"{application_id}.json"
        
        if not file_path.exists():
            logger.warning(f"Application not found: {application_id}")
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            return ApplicationData.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load application {application_id}: {e}", exc_info=True)
            return None
    
    def list_applications(self, status: Optional[str] = None, tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all applications, optionally filtered by status or tag.
        
        Args:
            status (str, optional): Filter by status
            tag (str, optional): Filter by tag
            
        Returns:
            List[Dict[str, Any]]: List of applications as dictionaries
        """
        applications = []
        
        for file_path in self.data_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Apply filters
                if status and data.get("status") != status:
                    continue
                if tag and tag not in data.get("tags", []):
                    continue
                
                # Add a summary of the application
                summary = {
                    "application_id": data.get("application_id"),
                    "company": data.get("company"),
                    "job_title": data.get("job_title"),
                    "status": data.get("status"),
                    "tags": data.get("tags", []),
                    "created_at": data.get("metadata", {}).get("created_at")
                }
                applications.append(summary)
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}", exc_info=True)
        
        # Sort by creation date (newest first)
        applications.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return applications 