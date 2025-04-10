"""
Job Finder
==========
This module discovers and monitors job listings from various sources.
"""

import os
import json
import requests
import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class JobListing:
    """Represents a job listing with all relevant details."""
    
    def __init__(self,
                 job_id: Optional[str] = None,
                 title: str = "",
                 company: str = "",
                 location: str = "",
                 description: str = "",
                 url: str = "",
                 source: str = "",
                 date_posted: Optional[str] = None,
                 salary: Optional[str] = None,
                 job_type: Optional[str] = None,
                 skills: Optional[List[str]] = None,
                 status: str = "new",
                 applied: bool = False,
                 application_date: Optional[str] = None,
                 notes: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a job listing.
        
        Args:
            job_id (str, optional): Unique identifier for the job
            title (str): Job title
            company (str): Company name
            location (str): Job location
            description (str): Job description
            url (str): URL of the job listing
            source (str): Source of the job listing (e.g., LinkedIn, Indeed)
            date_posted (str, optional): Date the job was posted
            salary (str, optional): Salary information
            job_type (str, optional): Job type (e.g., Full-time, Part-time)
            skills (List[str], optional): Required skills
            status (str): Status of the job (new, viewed, applied, rejected, etc.)
            applied (bool): Whether the user has applied for this job
            application_date (str, optional): Date the user applied
            notes (str, optional): User notes about the job
            metadata (Dict[str, Any], optional): Additional metadata
        """
        self.job_id = job_id or str(uuid.uuid4())
        self.title = title
        self.company = company
        self.location = location
        self.description = description
        self.url = url
        self.source = source
        self.date_posted = date_posted or datetime.now().isoformat()
        self.salary = salary
        self.job_type = job_type
        self.skills = skills or []
        self.status = status
        self.applied = applied
        self.application_date = application_date
        self.notes = notes
        self.metadata = metadata or {}
        
        # Add timestamp if not in metadata
        if "created_at" not in self.metadata:
            self.metadata["created_at"] = datetime.now().isoformat()
        self.metadata["updated_at"] = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the job listing to a dictionary."""
        return {
            "job_id": self.job_id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "description": self.description,
            "url": self.url,
            "source": self.source,
            "date_posted": self.date_posted,
            "salary": self.salary,
            "job_type": self.job_type,
            "skills": self.skills,
            "status": self.status,
            "applied": self.applied,
            "application_date": self.application_date,
            "notes": self.notes,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobListing':
        """Create a job listing from a dictionary."""
        return cls(
            job_id=data.get("job_id"),
            title=data.get("title", ""),
            company=data.get("company", ""),
            location=data.get("location", ""),
            description=data.get("description", ""),
            url=data.get("url", ""),
            source=data.get("source", ""),
            date_posted=data.get("date_posted"),
            salary=data.get("salary"),
            job_type=data.get("job_type"),
            skills=data.get("skills", []),
            status=data.get("status", "new"),
            applied=data.get("applied", False),
            application_date=data.get("application_date"),
            notes=data.get("notes"),
            metadata=data.get("metadata", {})
        )

class JobFinder:
    """Finds and tracks job listings from multiple sources."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the job finder.
        
        Args:
            data_dir (str, optional): Directory to store job listings
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            base_dir = Path(__file__).parent.parent.parent
            self.data_dir = base_dir / "data" / "jobs"
        
        # Create the data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Headers for HTTP requests to avoid being blocked
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        logger.info(f"Job finder initialized. Data directory: {self.data_dir}")
    
    def search_jobs(self, 
                    keywords: List[str], 
                    location: Optional[str] = None,
                    job_type: Optional[str] = None,
                    sources: Optional[List[str]] = None,
                    limit: int = 20) -> List[JobListing]:
        """
        Search for jobs across multiple sources.
        
        Args:
            keywords (List[str]): Keywords to search for
            location (str, optional): Location to search in
            job_type (str, optional): Type of job (full-time, part-time, etc.)
            sources (List[str], optional): Sources to search (indeed, linkedin, etc.)
            limit (int): Maximum number of jobs to return
            
        Returns:
            List[JobListing]: List of job listings
        """
        sources = sources or ["indeed", "linkedin"]
        all_jobs = []
        
        # Search each source
        for source in sources:
            try:
                if source.lower() == "indeed":
                    jobs = self._search_indeed(keywords, location, job_type, limit // len(sources))
                elif source.lower() == "linkedin":
                    jobs = self._search_linkedin(keywords, location, job_type, limit // len(sources))
                else:
                    logger.warning(f"Unknown job source: {source}")
                    continue
                
                all_jobs.extend(jobs)
                logger.info(f"Found {len(jobs)} jobs from {source}")
            
            except Exception as e:
                logger.error(f"Error searching {source}: {e}", exc_info=True)
        
        # Save all new jobs
        for job in all_jobs:
            self._save_job(job)
        
        # Return up to the limit
        return all_jobs[:limit]
    
    def _search_indeed(self, 
                       keywords: List[str],
                       location: Optional[str],
                       job_type: Optional[str],
                       limit: int) -> List[JobListing]:
        """
        Search for jobs on Indeed.
        
        Args:
            keywords (List[str]): Keywords to search for
            location (str, optional): Location to search in
            job_type (str, optional): Type of job
            limit (int): Maximum number of jobs to return
            
        Returns:
            List[JobListing]: List of job listings
        """
        # Note: This is a placeholder. Actual implementation would use Indeed's API
        # or web scraping, which requires careful implementation to avoid being blocked.
        logger.info("Indeed search is a placeholder. Would search for: " + ", ".join(keywords))
        
        # Return an empty list for now
        return []
    
    def _search_linkedin(self, 
                         keywords: List[str],
                         location: Optional[str],
                         job_type: Optional[str],
                         limit: int) -> List[JobListing]:
        """
        Search for jobs on LinkedIn.
        
        Args:
            keywords (List[str]): Keywords to search for
            location (str, optional): Location to search in
            job_type (str, optional): Type of job
            limit (int): Maximum number of jobs to return
            
        Returns:
            List[JobListing]: List of job listings
        """
        # Note: This is a placeholder. Actual implementation would use LinkedIn's API
        # or web scraping, which requires careful implementation to avoid being blocked.
        logger.info("LinkedIn search is a placeholder. Would search for: " + ", ".join(keywords))
        
        # Return an empty list for now
        return []
    
    def get_job_details(self, job_id: str) -> Optional[JobListing]:
        """
        Get details for a specific job.
        
        Args:
            job_id (str): ID of the job to get details for
            
        Returns:
            Optional[JobListing]: The job listing, or None if not found
        """
        file_path = self.data_dir / f"{job_id}.json"
        
        if not file_path.exists():
            logger.warning(f"Job not found: {job_id}")
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            return JobListing.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load job {job_id}: {e}", exc_info=True)
            return None
    
    def update_job_status(self, job_id: str, status: str, notes: Optional[str] = None) -> bool:
        """
        Update the status of a job.
        
        Args:
            job_id (str): ID of the job to update
            status (str): New status
            notes (str, optional): Additional notes
            
        Returns:
            bool: True if successful, False otherwise
        """
        job = self.get_job_details(job_id)
        
        if not job:
            return False
        
        job.status = status
        if notes:
            job.notes = notes
        
        job.metadata["updated_at"] = datetime.now().isoformat()
        
        return self._save_job(job)
    
    def mark_job_applied(self, job_id: str, application_date: Optional[str] = None, notes: Optional[str] = None) -> bool:
        """
        Mark a job as applied.
        
        Args:
            job_id (str): ID of the job to mark
            application_date (str, optional): Date of application
            notes (str, optional): Additional notes
            
        Returns:
            bool: True if successful, False otherwise
        """
        job = self.get_job_details(job_id)
        
        if not job:
            return False
        
        job.applied = True
        job.status = "applied"
        job.application_date = application_date or datetime.now().isoformat()
        if notes:
            job.notes = notes
        
        job.metadata["updated_at"] = datetime.now().isoformat()
        
        return self._save_job(job)
    
    def list_jobs(self, status: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        List all jobs, optionally filtered by status.
        
        Args:
            status (str, optional): Filter by status
            limit (int): Maximum number of jobs to return
            offset (int): Offset to start from
            
        Returns:
            List[Dict[str, Any]]: List of job summaries
        """
        jobs = []
        
        for file_path in self.data_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Apply filters
                if status and data.get("status") != status:
                    continue
                
                # Add a summary of the job
                summary = {
                    "job_id": data.get("job_id"),
                    "title": data.get("title"),
                    "company": data.get("company"),
                    "location": data.get("location"),
                    "url": data.get("url"),
                    "source": data.get("source"),
                    "status": data.get("status"),
                    "applied": data.get("applied", False),
                    "date_posted": data.get("date_posted"),
                    "application_date": data.get("application_date")
                }
                jobs.append(summary)
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}", exc_info=True)
        
        # Sort by date posted (newest first)
        jobs.sort(key=lambda x: x.get("date_posted", ""), reverse=True)
        
        # Apply limit and offset
        return jobs[offset:offset + limit]
    
    def _save_job(self, job: JobListing) -> bool:
        """
        Save a job listing to a file.
        
        Args:
            job (JobListing): The job listing to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            file_path = self.data_dir / f"{job.job_id}.json"
            
            with open(file_path, 'w') as f:
                json.dump(job.to_dict(), f, indent=4)
            
            logger.info(f"Saved job {job.job_id} ({job.title} at {job.company})")
            return True
        except Exception as e:
            logger.error(f"Failed to save job {job.job_id}: {e}", exc_info=True)
            return False
    
    def cleanup_old_jobs(self, days: int = 30) -> int:
        """
        Delete jobs older than a certain number of days.
        
        Args:
            days (int): Number of days after which jobs are considered old
            
        Returns:
            int: Number of jobs deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        for file_path in self.data_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Check if the job is old
                created_at = data.get("metadata", {}).get("created_at")
                if created_at:
                    created_date = datetime.fromisoformat(created_at)
                    if created_date < cutoff_date:
                        # Delete the file
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info(f"Deleted old job: {data.get('job_id')}")
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}", exc_info=True)
        
        logger.info(f"Cleaned up {deleted_count} old jobs")
        return deleted_count 