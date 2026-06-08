"""
LLM Service - Resume Tailoring & Cover Letter Generation

Updated with latest langchain-openai imports
"""

import json
import logging
from typing import Dict, Optional, Any
from langchain_openai import ChatOpenAI  # UPDATED import
from app.core.config import settings

logger = logging.getLogger(__name__)

class ResumeTailoringService:
    """Resume Tailoring using LLM"""
    
    def __init__(self, model: str = "gpt-4"):
        """Initialize with OpenAI LLM"""
        logger.info(f"Initializing LLM Service with model: {model}")
        
        self.llm = ChatOpenAI(
            model_name=model,
            temperature=0.3,
            api_key=settings.OPENAI_API_KEY,
            max_retries=2,
            timeout=60
        )
        
        logger.info("✅ LLM Service initialized")
    
    def tailor_resume(
        self,
        original_resume: Dict[str, Any],
        job_description: str,
        extracted_skills: list,
        user_preferences: Dict = None
    ) -> Dict:
        """Tailor resume to match job posting"""
        
        logger.info("Starting resume tailoring...")
        
        user_preferences = user_preferences or {}
        
        system_prompt = """You are an expert resume writer specializing in ATS optimization and recruiter attraction.

YOUR CORE RULES (CRITICAL):
1. NEVER add false experiences - only rephrase existing ones
2. NEVER change job titles or dates
3. NEVER fabricate skills or achievements
4. Match 70%+ of job description keywords
5. Keep timeline and positions exactly the same
6. Output ONLY valid JSON (no markdown, no explanations)

YOUR TASK:
1. Read the original resume carefully
2. Compare with job requirements
3. Reword achievements to highlight relevant skills
4. Optimize for ATS by using job keywords
5. Return ONLY JSON format below

JSON OUTPUT FORMAT (IMPORTANT - MUST BE VALID):
{
    "summary": "Professional summary tailored to the role - 2-3 sentences",
    "experience": [
        {
            "title": "Same job title as original",
            "company": "Same company as original",
            "duration": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
            "achievements": [
                "Achievement 1 reworded to match job keywords",
                "Achievement 2 emphasizing relevant skills"
            ]
        }
    ],
    "skills": ["Skill1", "Skill2", "Skill3"],
    "education": [
        {
            "degree": "Same as original",
            "school": "Same as original",
            "graduation_year": 2020
        }
    ],
    "ats_notes": [
        "Added keyword: machine learning",
        "Emphasized: AWS experience",
        "Highlighted: Leadership in team management"
    ]
}"""
        
        user_message = f"""
ORIGINAL RESUME:
{json.dumps(original_resume, indent=2)}

TARGET JOB DESCRIPTION:
{job_description}

KEY SKILLS TO EMPHASIZE (found in job posting):
{', '.join(extracted_skills[:10]) if extracted_skills else "No specific skills extracted"}

USER PREFERENCES:
- Focus areas: {', '.join(user_preferences.get('focus_areas', ['general'])) if user_preferences.get('focus_areas') else 'general'}
- Style: {user_preferences.get('style', 'professional')}

Now generate the tailored resume. Remember: ONLY output JSON, nothing else."""
        
        try:
            logger.info("Calling OpenAI API for resume tailoring...")
            
            from langchain_core.messages import HumanMessage, SystemMessage
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            response = self.llm.invoke(messages)
            response_text = response.content
            
            logger.info("Got response from OpenAI")
            
            # Parse JSON
            try:
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0]
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0]
                
                generated_content = json.loads(response_text.strip())
                
                logger.info("✅ Resume tailored successfully")
                return {
                    "success": True,
                    "generated_content": generated_content,
                    "tokens_used": len(response_text.split())
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response: {response_text[:500]}")
                return {
                    "success": False,
                    "error": "Invalid JSON from LLM",
                    "raw_response": response_text[:500]
                }
        
        except Exception as e:
            logger.error(f"LLM Error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_cover_letter(
        self,
        user_resume: Dict[str, Any],
        job_description: str,
        company_name: str,
        job_title: str,
        tone: str = "professional"
    ) -> str:
        """Generate cover letter for job application"""
        
        logger.info(f"Generating cover letter for {company_name}")
        
        tone_instructions = {
            "professional": "Formal, respectful, achievement-focused, business-like",
            "friendly": "Warm, approachable, enthusiastic, collaborative",
            "assertive": "Confident, direct, impact-focused, leadership-oriented"
        }
        
        creative_llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.5,
            api_key=settings.OPENAI_API_KEY,
            max_retries=2
        )
        
        system_prompt = f"""You are an expert cover letter writer.

Your task is to write a compelling cover letter that:
1. References 3-4 specific requirements from the job posting
2. Shows genuine interest in {company_name}
3. Connects user's experience to role needs
4. Tone: {tone_instructions.get(tone, 'professional')}
5. Length: 3-4 paragraphs, approximately 250-300 words
6. Professional, error-free writing

Format:
Dear Hiring Manager,

[Opening paragraph: why you're interested + 1 key qualification]
[Middle paragraph(s): relevant experience + achievements + job requirements]
[Closing paragraph: enthusiasm + call to action]

Sincerely,
[Name]

Important:
- Do NOT include name or contact info (user will add)
- Do NOT use placeholders like [COMPANY] - use actual names provided
- Be specific - reference actual job requirements
- Show research/knowledge of company if possible
- NO generic language"""
        
        user_message = f"""Write a cover letter for this position:

COMPANY: {company_name}
POSITION: {job_title}

USER'S BACKGROUND:
{json.dumps(user_resume, indent=2)}

JOB POSTING:
{job_description}

Generate the cover letter (without name and contact info):"""
        
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ]
            
            logger.info("Calling OpenAI API for cover letter...")
            response = creative_llm.invoke(messages)
            cover_letter = response.content
            
            logger.info("✅ Cover letter generated")
            return cover_letter
            
        except Exception as e:
            logger.error(f"Cover letter generation error: {str(e)}")
            return f"Error generating cover letter: {str(e)}"
    
    def calculate_ats_score(
        self,
        resume_text: str,
        job_description: str
    ) -> float:
        """Calculate ATS compatibility score (0-1)"""
        
        job_words = set(job_description.lower().split())
        resume_words = set(resume_text.lower().split())
        
        matches = len(job_words & resume_words)
        total = len(job_words)
        
        if total == 0:
            return 0.0
        
        score = min(matches / total * 1.5, 1.0)
        
        return round(score, 2)