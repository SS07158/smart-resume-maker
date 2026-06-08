"""
Resume Parser Service

WHY SEPARATE SERVICE:
- Parses PDF/DOCX into structured JSON
- Extracts skills, experience, education
- Cleans and normalizes data
- Reusable across endpoints
"""

import json
import logging
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)

class ResumeParser:
    """
    Parse resumes from text into structured JSON
    
    This handles free text format resumes
    Real world: You'd use libraries like:
    - py-resume-parser (free)
    - pdfplumber (PDF extraction)
    - python-docx (DOCX extraction)
    """
    
    @staticmethod
    def extract_contact_info(text: str) -> Dict:
        """Extract email, phone, location"""
        
        # Email regex
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        
        # Phone regex (various formats)
        phone_pattern = r'(?:\+\d{1,3})?[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
        phones = re.findall(phone_pattern, text)
        
        return {
            "email": emails[0] if emails else None,
            "phone": phones[0] if phones else None,
            "location": None  # Would need NLP to extract
        }
    
    @staticmethod
    def extract_skills(text: str) -> Dict[str, List[str]]:
        """
        Extract skills from resume text
        
        WHY THIS MATTERS:
        - Skills are KEY for resume tailoring
        - Need to match with job requirements
        - Used for ATS optimization
        """
        
        # Common programming skills database
        tech_skills = {
            "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust",
            "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis",
            "FastAPI", "Django", "Flask", "Node.js", "Express", "React", "Vue", "Angular",
            "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Linux",
            "Git", "Jenkins", "GitHub Actions", "DevOps",
            "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "LLM",
            "API Design", "REST", "GraphQL", "Microservices"
        }
        
        # Soft skills
        soft_skills = {
            "Leadership", "Communication", "Problem Solving", "Project Management",
            "Team Collaboration", "Time Management", "Critical Thinking", "Creativity",
            "Agile", "Scrum"
        }
        
        text_lower = text.lower()
        found_tech = []
        found_soft = []
        
        # Find tech skills
        for skill in tech_skills:
            if skill.lower() in text_lower:
                found_tech.append(skill)
        
        # Find soft skills
        for skill in soft_skills:
            if skill.lower() in text_lower:
                found_soft.append(skill)
        
        return {
            "programming": list(set(found_tech)),  # Remove duplicates
            "soft_skills": list(set(found_soft))
        }
    
    @staticmethod
    def extract_experience(text: str) -> List[Dict]:
        """
        Extract work experience
        
        Looks for sections with:
        - Job title
        - Company name
        - Dates
        - Achievements (bullet points)
        """
        
        experiences = []
        
        # Split by common section headers
        experience_section = ""
        lines = text.split('\n')
        in_experience = False
        
        for line in lines:
            lower = line.lower()
            
            if any(keyword in lower for keyword in ['experience', 'work history', 'professional experience']):
                in_experience = True
                continue
            
            if any(keyword in lower for keyword in ['education', 'skills', 'projects', 'certifications']):
                in_experience = False
                continue
            
            if in_experience:
                experience_section += line + '\n'
        
        # Parse experiences (simple pattern matching)
        # In production, use more sophisticated NLP
        current_job = None
        for line in experience_section.split('\n'):
            line = line.strip()
            
            if not line:
                continue
            
            # Save previous job if exists
            if line[0].isupper() and current_job:
                experiences.append(current_job)
            
            # Start new job if looks like title
            if any(char in line for char in ['|', ' - ', 'at']) and len(line) > 10:
                current_job = {
                    "title": line.split('|')[0].strip() if '|' in line else line,
                    "company": line.split('|')[1].strip() if '|' in line else "Unknown",
                    "duration": {},
                    "achievements": []
                }
            # Add achievement (bullet point)
            elif current_job and line.startswith(('•', '-', '*')):
                current_job["achievements"].append(line[1:].strip())
        
        if current_job:
            experiences.append(current_job)
        
        return experiences
    
    @staticmethod
    def extract_education(text: str) -> List[Dict]:
        """Extract education information"""
        
        educations = []
        
        # Find education section
        education_section = ""
        lines = text.split('\n')
        in_education = False
        
        for line in lines:
            lower = line.lower()
            
            if 'education' in lower:
                in_education = True
                continue
            
            if in_education and any(keyword in lower for keyword in ['experience', 'skills', 'projects']):
                break
            
            if in_education:
                education_section += line + '\n'
        
        # Parse education
        for line in education_section.split('\n'):
            line = line.strip()
            if line and any(degree in line for degree in ['B.S.', 'B.A.', 'M.S.', 'M.A.', 'PhD', 'B.Tech', 'M.Tech']):
                educations.append({
                    "degree": line.split('-')[0].strip() if '-' in line else line,
                    "school": line.split('-')[1].strip() if '-' in line else "Unknown",
                    "graduation_year": None
                })
        
        return educations
    
    @staticmethod
    def parse(text: str, name: str = "Unknown") -> Dict:
        """
        Main parsing function
        
        Converts raw resume text into structured JSON
        
        Returns:
        {
            "name": "John Doe",
            "contact": {...},
            "summary": "...",
            "experience": [...],
            "education": [...],
            "skills": {...}
        }
        """
        
        logger.info("Parsing resume...")
        
        contact = ResumeParser.extract_contact_info(text)
        skills = ResumeParser.extract_skills(text)
        experience = ResumeParser.extract_experience(text)
        education = ResumeParser.extract_education(text)
        
        # Extract summary (first non-empty paragraph)
        summary = ""
        for line in text.split('\n'):
            if len(line.strip()) > 50 and not any(char in line for char in ['•', '-', '*']):
                summary = line.strip()
                break
        
        parsed = {
            "name": name,
            "contact": contact,
            "summary": summary,
            "experience": experience,
            "education": education,
            "skills": skills
        }
        
        logger.info(f"✅ Resume parsed: {len(experience)} jobs, {len(education)} degrees")
        
        return parsed
