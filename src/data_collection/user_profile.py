"""
User Profile Module
==================
This module handles user profile data and operations.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

class Education(BaseModel):
    """Education history details."""
    institution: str
    degree: str
    field_of_study: str
    start_date: str
    end_date: Optional[str] = None
    gpa: Optional[float] = None
    description: Optional[str] = None
    
    @validator('end_date')
    def validate_dates(cls, end_date, values):
        """Validate that end_date is after start_date."""
        if end_date and 'start_date' in values:
            start = datetime.strptime(values['start_date'], '%Y-%m')
            end = datetime.strptime(end_date, '%Y-%m')
            if end < start:
                raise ValueError("End date must be after start date")
        return end_date

class Experience(BaseModel):
    """Work experience details."""
    company: str
    title: str
    location: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    current: bool = False
    description: str
    
    @validator('end_date')
    def validate_dates(cls, end_date, values):
        """Validate that end_date is after start_date or None if current is True."""
        if values.get('current', False) and end_date:
            raise ValueError("End date should be empty for current positions")
        
        if end_date and 'start_date' in values:
            start = datetime.strptime(values['start_date'], '%Y-%m')
            end = datetime.strptime(end_date, '%Y-%m')
            if end < start:
                raise ValueError("End date must be after start date")
        return end_date

class Skill(BaseModel):
    """Skill details."""
    name: str
    level: Optional[str] = None  # e.g., "Beginner", "Intermediate", "Advanced"
    years: Optional[int] = None

class UserProfile(BaseModel):
    """Full user profile containing all job-related information."""
    # Personal Information
    full_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    
    # Professional Summary
    summary: Optional[str] = None
    
    # Education
    education: List[Education] = Field(default_factory=list)
    
    # Work Experience
    experience: List[Experience] = Field(default_factory=list)
    
    # Skills
    skills: List[Skill] = Field(default_factory=list)
    
    # Job Preferences
    desired_role: Optional[str] = None
    desired_industry: Optional[List[str]] = None
    desired_location: Optional[List[str]] = None
    remote_preference: Optional[str] = None  # "Remote", "Hybrid", "On-site"
    salary_expectation: Optional[str] = None
    
    # Additional Information
    languages: Optional[List[Dict[str, str]]] = None
    certifications: Optional[List[Dict[str, str]]] = None
    projects: Optional[List[Dict[str, str]]] = None
    
    # Application Preferences
    response_templates: Dict[str, str] = Field(default_factory=dict)
    
    # Learning Data
    observed_applications: List[str] = Field(default_factory=list)
    
    # Meta Data
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    @validator('updated_at', always=True)
    def update_timestamp(cls, v):
        """Automatically update the updated_at timestamp."""
        return datetime.now().isoformat()

class UserProfileManager:
    """Manages user profile data operations."""
    
    def __init__(self, profile_path: Optional[str] = None):
        """
        Initialize the UserProfileManager.
        
        Args:
            profile_path (str, optional): Path to the profile JSON file. Defaults to None.
        """
        if profile_path:
            self.profile_path = Path(profile_path)
        else:
            base_dir = Path(__file__).parent.parent.parent
            self.profile_path = base_dir / "data" / "user_profile.json"
        
        self.profile = self._load_profile()
    
    def _load_profile(self) -> UserProfile:
        """
        Load the user profile from the JSON file.
        
        Returns:
            UserProfile: The loaded user profile or a new one if it doesn't exist.
        """
        try:
            if self.profile_path.exists():
                with open(self.profile_path, 'r') as f:
                    data = json.load(f)
                return UserProfile(**data)
            else:
                logger.info(f"Profile file not found at {self.profile_path}. Creating a new one.")
                return UserProfile(full_name="", email="")
        except Exception as e:
            logger.error(f"Error loading profile: {e}", exc_info=True)
            return UserProfile(full_name="", email="")
    
    def save_profile(self) -> bool:
        """
        Save the user profile to the JSON file.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(self.profile_path.parent, exist_ok=True)
            
            # Update timestamp
            self.profile.updated_at = datetime.now().isoformat()
            
            # Save to file
            with open(self.profile_path, 'w') as f:
                json.dump(self.profile.dict(), f, indent=4)
            
            logger.info(f"Profile saved successfully to {self.profile_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving profile: {e}", exc_info=True)
            return False
    
    def update_profile(self, data: Dict[str, Any]) -> bool:
        """
        Update the user profile with the provided data.
        
        Args:
            data (Dict[str, Any]): The data to update the profile with.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Update profile with new data
            for key, value in data.items():
                if hasattr(self.profile, key):
                    setattr(self.profile, key, value)
            
            # Save updated profile
            return self.save_profile()
        except Exception as e:
            logger.error(f"Error updating profile: {e}", exc_info=True)
            return False
    
    def add_education(self, education: Dict[str, Any]) -> bool:
        """
        Add an education entry to the profile.
        
        Args:
            education (Dict[str, Any]): The education data.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            edu = Education(**education)
            self.profile.education.append(edu)
            return self.save_profile()
        except Exception as e:
            logger.error(f"Error adding education: {e}", exc_info=True)
            return False
    
    def add_experience(self, experience: Dict[str, Any]) -> bool:
        """
        Add a work experience entry to the profile.
        
        Args:
            experience (Dict[str, Any]): The experience data.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            exp = Experience(**experience)
            self.profile.experience.append(exp)
            return self.save_profile()
        except Exception as e:
            logger.error(f"Error adding experience: {e}", exc_info=True)
            return False
    
    def add_skill(self, skill: Dict[str, Any]) -> bool:
        """
        Add a skill to the profile.
        
        Args:
            skill (Dict[str, Any]): The skill data.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            sk = Skill(**skill)
            self.profile.skills.append(sk)
            return self.save_profile()
        except Exception as e:
            logger.error(f"Error adding skill: {e}", exc_info=True)
            return False
    
    def add_observed_application(self, application_id: str) -> bool:
        """
        Add an observed application to the profile.
        
        Args:
            application_id (str): The ID of the observed application.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if application_id not in self.profile.observed_applications:
                self.profile.observed_applications.append(application_id)
                return self.save_profile()
            return True
        except Exception as e:
            logger.error(f"Error adding observed application: {e}", exc_info=True)
            return False 