"""
Job Description Parser & Extractor Service

WHY:
- Extract KEY features from job postings
- These features used for resume tailoring
- Enable skill matching
- Determine seniority level
"""

import re
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class JobDescriptionExtractor:
    """
    Extract job posting features
    
    Features extracted:
    - Skills (technical + soft)
    - Requirements (years exp, education)
    - Seniority level
    - Company size hints
    - Culture indicators
    """
    
    # Skills database
    TECH_SKILLS = {
        "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go", "Rust",
        "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "FastAPI", "Django", "Flask", "Node.js", "Express", "React", "Vue", "Angular",
        "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Terraform", "Linux",
        "Git", "CI/CD", "Jenkins", "GitHub Actions", "GitLab",
        "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "LLM", "NLP",
        "REST", "GraphQL", "API Design", "Microservices", "Design Patterns"
    }
    
    @staticmethod
    def extract_skills(text: str) -> List[str]:
        """
        Extract technical skills from job posting
        
        WHY THIS IS CRUCIAL:
        - Skills are what we match to resume
        - Used for resume keyword optimization
        - Key for ATS matching
        """
        
        found_skills = []
        text_lower = text.lower()
        
        for skill in JobDescriptionExtractor.TECH_SKILLS:
            # Case-insensitive search
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        # Extract years of experience
        years_pattern = r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience|exp)"
        years_match = re.search(years_pattern, text_lower)
        
        if years_match:
            years = years_match.group(1)
            found_skills.append(f"{years}+ years experience")
        
        logger.info(f"Found skills: {found_skills}")
        return found_skills
    
    @staticmethod
    def extract_requirements(text: str) -> Dict:
        """
        Extract structured requirements
        
        Returns:
        {
            "required_skills": [...],
            "nice_to_have": [...],
            "years_of_experience": 5,
            "responsibilities": [...],
            "education": "Bachelor's degree"
        }
        """
        
        requirements = {
            "required_skills": [],
            "nice_to_have": [],
            "years_of_experience": None,
            "responsibilities": [],
            "education": None
        }
        
        text_lower = text.lower()
        
        # Extract years of experience
        years_pattern = r"(\d+)\+?\s*(?:years?|yrs?)"
        years_match = re.search(years_pattern, text_lower)
        if years_match:
            requirements["years_of_experience"] = int(years_match.group(1))
        
        # Extract education requirements
        if "bachelor" in text_lower:
            requirements["education"] = "Bachelor's Degree"
        elif "master" in text_lower:
            requirements["education"] = "Master's Degree"
        
        # Extract responsibilities (lines with bullets)
        responsibilities = []
        for line in text.split('\n'):
            if line.strip().startswith(('•', '-', '*')):
                resp = line.strip()[1:].strip()
                if len(resp) > 10:
                    responsibilities.append(resp)
        
        requirements["responsibilities"] = responsibilities[:5]  # Top 5
        
        return requirements
    
    @staticmethod
    def extract_seniority_level(text: str) -> str:
        """
        Determine job seniority level
        
        Returns: 'entry', 'mid', 'senior', 'lead'
        
        WHY:
        - Affects how we tailor resume
        - Determines which experiences to highlight
        """
        
        text_lower = text.lower()
        
        # Check for lead/principal
        if any(word in text_lower for word in ['lead', 'principal', 'architect', 'director', 'head of']):
            return "lead"
        
        # Check for senior
        if any(word in text_lower for word in ['senior', 'staff', 'expert']):
            return "senior"
        
        # Check for entry
        if any(word in text_lower for word in ['junior', 'entry', 'graduate', 'entry-level']):
            return "entry"
        
        # Default to mid
        return "mid"
    
    @staticmethod
    def extract_company_info(text: str) -> Dict:
        """Extract company details if available"""
        
        return {
            "company_name": None,  # Would need more sophisticated extraction
            "job_title": None,
            "culture_hints": JobDescriptionExtractor._extract_culture(text)
        }
    
    @staticmethod
    def _extract_culture(text: str) -> List[str]:
        """Extract company culture hints"""
        
        culture_keywords = {
            "fast-paced": ["fast", "rapid", "agile", "quick"],
            "collaborative": ["team", "collaboration", "together", "cross-functional"],
            "innovative": ["cutting-edge", "innovation", "latest", "emerging"],
            "stable": ["established", "proven", "mature", "market leader"]
        }
        
        detected = []
        text_lower = text.lower()
        
        for culture, keywords in culture_keywords.items():
            if any(kw in text_lower for kw in keywords):
                detected.append(culture)
        
        return detected