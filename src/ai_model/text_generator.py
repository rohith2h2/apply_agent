"""
AI Text Generator
===============
This module uses OpenAI's API to generate text responses for job applications.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import openai

from src.data_collection.user_profile import UserProfile
from src.data_collection.application_collector import ApplicationData, ApplicationField

logger = logging.getLogger(__name__)

class TextGenerator:
    """
    Text generator using OpenAI's API to generate responses for job applications.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the text generator.
        
        Args:
            api_key (str, optional): OpenAI API key. If not provided, will try to get from environment.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("No OpenAI API key provided. Text generation will not work.")
        else:
            openai.api_key = self.api_key
    
    def generate_response(self, 
                          field: ApplicationField, 
                          user_profile: UserProfile,
                          job_title: str,
                          job_description: str,
                          similar_responses: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Generate a response for a given application field.
        
        Args:
            field (ApplicationField): The field to generate a response for
            user_profile (UserProfile): The user's profile
            job_title (str): The job title
            job_description (str): The job description
            similar_responses (List[Dict[str, str]], optional): Similar responses from previous applications
            
        Returns:
            str: The generated response
        """
        if not self.api_key:
            raise ValueError("No OpenAI API key provided. Cannot generate text.")
        
        # Create prompt based on field type and available data
        prompt = self._create_prompt(field, user_profile, job_title, job_description, similar_responses)
        
        try:
            # Call OpenAI API to generate text
            response = openai.chat.completions.create(
                model="gpt-4-0125-preview",  # or another appropriate model
                messages=[
                    {"role": "system", "content": "You are an AI assistant helping a job applicant complete application forms. Generate a professional, personalized response based on the applicant's profile and the job description. Match their writing style from previous applications."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7,
            )
            
            # Extract and return the generated text
            generated_text = response.choices[0].message.content.strip()
            logger.info(f"Generated text for field: {field.name}")
            return generated_text
        
        except Exception as e:
            logger.error(f"Error generating text: {e}", exc_info=True)
            return ""
    
    def _create_prompt(self, 
                       field: ApplicationField, 
                       user_profile: UserProfile,
                       job_title: str,
                       job_description: str,
                       similar_responses: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Create a prompt for the OpenAI API.
        
        Args:
            field (ApplicationField): The field to generate a response for
            user_profile (UserProfile): The user's profile
            job_title (str): The job title
            job_description (str): The job description
            similar_responses (List[Dict[str, str]], optional): Similar responses from previous applications
            
        Returns:
            str: The prompt for the OpenAI API
        """
        # Start with basic context
        prompt = f"Generate a response for the field '{field.name}' in a job application for the position of '{job_title}'.\n\n"
        
        # Add job description
        if job_description:
            prompt += f"Job Description:\n{job_description}\n\n"
        
        # Add user profile information
        prompt += "Applicant Profile:\n"
        prompt += f"Name: {user_profile.full_name}\n"
        prompt += f"Email: {user_profile.email}\n"
        
        if user_profile.summary:
            prompt += f"Professional Summary: {user_profile.summary}\n"
        
        # Add relevant experience
        if user_profile.experience:
            prompt += "\nRelevant Experience:\n"
            for exp in user_profile.experience:
                prompt += f"- {exp.title} at {exp.company} ({exp.start_date} to {exp.end_date if not exp.current else 'Present'})\n"
                prompt += f"  {exp.description}\n"
        
        # Add relevant skills
        if user_profile.skills:
            prompt += "\nSkills:\n"
            for skill in user_profile.skills:
                prompt += f"- {skill.name}"
                if skill.level:
                    prompt += f" ({skill.level})"
                prompt += "\n"
        
        # Add similar responses from previous applications if available
        if similar_responses:
            prompt += "\nApplicant's previous responses to similar questions:\n"
            for i, response in enumerate(similar_responses, 1):
                prompt += f"Example {i} ({response.get('field_name', 'Unknown Field')}):\n{response.get('value', '')}\n\n"
            prompt += "Please generate a response that matches the applicant's writing style in previous applications.\n"
        
        # Add specific instructions based on field type
        if field.type == "textarea" or field.name.lower() in ["cover letter", "personal statement", "why do you want to work here"]:
            prompt += "\nThis appears to be a longer form response. Please generate a detailed, personalized response that highlights the applicant's relevant experience and skills for this position.\n"
        elif "salary" in field.name.lower() or "compensation" in field.name.lower():
            prompt += "\nThis is a salary expectation question. Provide a reasonable salary range based on the position and the applicant's experience.\n"
        elif "availability" in field.name.lower() or "start date" in field.name.lower():
            prompt += "\nThis is asking about availability or start date. Provide a professional response indicating prompt availability.\n"
        
        # Add field-specific constraints
        if field.options:
            prompt += f"\nThis field has the following options to choose from: {', '.join(field.options)}. Select the most appropriate option.\n"
        
        # Final instructions
        prompt += "\nPlease provide a professional, concise, and personalized response appropriate for a job application. Focus on relevant information for this specific position."
        
        return prompt
    
    def learn_from_applications(self, applications: List[ApplicationData], user_profile: UserProfile) -> Dict[str, Any]:
        """
        Learn from previous applications to improve future responses.
        
        Args:
            applications (List[ApplicationData]): Previous applications to learn from
            user_profile (UserProfile): The user's profile
            
        Returns:
            Dict[str, Any]: Learning results with patterns and templates
        """
        if len(applications) < 1:
            logger.warning("Not enough applications to learn from")
            return {"status": "error", "message": "Not enough applications to learn from"}
        
        try:
            # Extract all fields from all applications
            all_fields = []
            for app in applications:
                for field in app.fields:
                    all_fields.append({
                        "application_id": app.application_id,
                        "company": app.company,
                        "job_title": app.job_title,
                        "field_name": field.name,
                        "field_type": field.type,
                        "value": field.value,
                        "section": field.section
                    })
            
            # Group similar fields
            field_groups = self._group_similar_fields(all_fields)
            
            # Extract patterns and templates
            patterns = {}
            for group_name, fields in field_groups.items():
                patterns[group_name] = self._extract_pattern(fields, group_name)
            
            # Save learning results
            learning_results = {
                "status": "success",
                "field_patterns": patterns,
                "applications_analyzed": len(applications),
                "fields_analyzed": len(all_fields)
            }
            
            logger.info(f"Learned from {len(applications)} applications with {len(all_fields)} fields")
            return learning_results
        
        except Exception as e:
            logger.error(f"Error learning from applications: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}
    
    def _group_similar_fields(self, fields: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group similar fields together based on their names.
        
        Args:
            fields (List[Dict[str, Any]]): List of fields from applications
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Groups of similar fields
        """
        field_groups = {}
        
        # Common field categories
        categories = {
            "name": ["name", "full name", "first name", "last name"],
            "email": ["email", "email address"],
            "phone": ["phone", "phone number", "mobile", "cell"],
            "address": ["address", "street address", "city", "state", "zip", "postal code"],
            "cover_letter": ["cover letter", "cover note", "letter of interest", "introduction", "why do you want to work here"],
            "experience": ["experience", "work experience", "work history", "employment history"],
            "education": ["education", "educational background", "academic background", "degree", "qualification"],
            "skills": ["skills", "technical skills", "competencies", "abilities"],
            "references": ["references", "professional references", "referees"],
            "availability": ["availability", "start date", "notice period"],
            "salary": ["salary", "salary expectation", "compensation", "desired pay", "wage"]
        }
        
        # Group fields by category
        for field in fields:
            field_name = field["field_name"].lower()
            assigned = False
            
            for category, keywords in categories.items():
                if any(keyword in field_name for keyword in keywords):
                    if category not in field_groups:
                        field_groups[category] = []
                    field_groups[category].append(field)
                    assigned = True
                    break
            
            if not assigned:
                # Put in miscellaneous group
                if "other" not in field_groups:
                    field_groups["other"] = []
                field_groups["other"].append(field)
        
        return field_groups
    
    def _extract_pattern(self, fields: List[Dict[str, Any]], category: str) -> Dict[str, Any]:
        """
        Extract patterns from similar fields to use as templates.
        
        Args:
            fields (List[Dict[str, Any]]): Similar fields
            category (str): Field category
            
        Returns:
            Dict[str, Any]: Extracted pattern
        """
        if not fields:
            return {"pattern_type": "empty", "template": ""}
        
        # For short fields, just use the values
        if category in ["name", "email", "phone", "address"]:
            return {
                "pattern_type": "direct",
                "examples": [field["value"] for field in fields if field["value"]]
            }
        
        # For longer text fields, analyze with OpenAI to extract patterns
        if category in ["cover_letter", "experience", "skills"]:
            # Get examples with non-empty values
            examples = [field["value"] for field in fields if field["value"] and len(field["value"]) > 20]
            
            if not examples:
                return {"pattern_type": "empty", "template": ""}
            
            try:
                # Use OpenAI to analyze patterns
                prompt = f"Analyze the following responses to '{category}' questions in job applications from the same person:\n\n"
                for i, example in enumerate(examples[:3], 1):  # Limit to 3 examples to avoid token limits
                    prompt += f"Example {i}:\n{example}\n\n"
                
                prompt += "\nPlease identify:\n1. Common themes and topics the applicant mentions\n2. Their writing style and tone\n3. How they structure their responses\n4. Key phrases or approaches they use repeatedly\n\nProvide a template that captures their writing style for future '{category}' responses."
                
                response = openai.chat.completions.create(
                    model="gpt-4-0125-preview",
                    messages=[
                        {"role": "system", "content": "You are analyzing job application responses to extract writing patterns and templates."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.7,
                )
                
                analysis = response.choices[0].message.content.strip()
                
                return {
                    "pattern_type": "analyzed",
                    "analysis": analysis,
                    "examples": examples[:2]  # Include a couple of examples
                }
            
            except Exception as e:
                logger.error(f"Error analyzing patterns: {e}", exc_info=True)
                return {
                    "pattern_type": "examples",
                    "examples": examples[:2]  # Fallback to just including examples
                }
        
        # For other fields, just include examples
        return {
            "pattern_type": "examples",
            "examples": [field["value"] for field in fields if field["value"]][:3]
        } 