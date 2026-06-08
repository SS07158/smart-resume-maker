"""
Resume & Cover Letter Generation Endpoints
THE CORE AI ENDPOINTS - This is where the magic happens!
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database import User, Resume, JobDescription, ResumeVariant, CoverLetter, get_db
from app.models.schemas import GenerateResumeVariantRequest, GenerateCoverLetterRequest
from app.api.auth import get_current_user
from app.services.llm_service import ResumeTailoringService
from app.services.embeddings_service import EmbeddingsService
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
llm_service = ResumeTailoringService()
embeddings_service = EmbeddingsService()

# ==================== GENERATE RESUME VARIANT ====================

@router.post("/resume-variant", summary="Generate tailored resume")
async def generate_resume_variant(
    request: GenerateResumeVariantRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    🚀 **Generate a resume tailored to a specific job!**
    
    **Requires Authorization** - Click Authorize button first!
    
    This is the core feature - uses AI to:
    1. Take your original resume
    2. Analyze the job description
    3. Reword achievements to match job keywords
    4. Optimize for ATS (Applicant Tracking Systems)
    5. Return a tailored resume
    
    **What you get back:**
    - Tailored resume content (optimized for the job)
    - ATS Score (0-1: how likely to pass ATS screening)
    - Match Score (0-1: how well resume matches job)
    - Ready to download as PDF or DOCX
    
    **Example request:**
    ```json
    {
        "resume_id": "paste-resume-id-here",
        "job_description_id": "paste-job-id-here",
        "user_preferences": {
            "focus_areas": ["leadership", "scalability", "cloud"],
            "style": "professional"
        }
    }
    ```
    
    **How to use:**
    1. First, register/login (Auth > Login)
    2. Upload your resume (Resumes > Upload)
    3. Submit a job description (Job Descriptions > Submit)
    4. Copy the IDs from steps 2 & 3
    5. Paste IDs here and click Execute!
    """
    
    try:
        # Get original resume
        resume = db.query(Resume).filter(
            Resume.id == request.resume_id,
            Resume.user_id == current_user.id
        ).first()
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        # Get job description
        job = db.query(JobDescription).filter(
            JobDescription.id == request.job_description_id,
            JobDescription.user_id == current_user.id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job description not found"
            )
        
        logger.info(f"Generating resume variant for user {current_user.email}")
        logger.info(f"  Resume: {resume.id}")
        logger.info(f"  Job: {job.id} ({job.company_name} - {job.job_title})")
        
        # Check for existing variant
        existing_variant = db.query(ResumeVariant).filter(
            ResumeVariant.original_resume_id == resume.id,
            ResumeVariant.job_description_id == job.id
        ).first()
        
        if existing_variant:
            logger.info(f"Found existing variant: {existing_variant.id} (reusing)")
            return {
                "status": "success",
                "variant_id": existing_variant.id,
                "generated_content": existing_variant.generated_content,
                "ats_score": existing_variant.ats_score,
                "match_score": existing_variant.match_score,
                "cached": True,
                "message": "Using previously generated variant for this job (saved on API costs!)"
            }
        
        # Generate new variant with LLM
        logger.info("Generating new variant with GPT-4...")
        
        result = llm_service.tailor_resume(
            original_resume=resume.original_content,
            job_description=job.raw_text,
            extracted_skills=job.extracted_skills or [],
            user_preferences=request.user_preferences or {}
        )
        
        if not result["success"]:
            logger.error(f"LLM generation failed: {result.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate variant: {result.get('error')}"
            )
        
        # Calculate ATS score
        generated_text = json.dumps(result["generated_content"])
        ats_score = llm_service.calculate_ats_score(
            generated_text,
            job.raw_text
        )
        
        # Calculate match score using embeddings
        match_score = embeddings_service.calculate_similarity(
            generated_text,
            job.raw_text
        )
        
        logger.info(f"ATS Score: {ats_score}, Match Score: {match_score}")
        
        # Store variant
        variant = ResumeVariant(
            original_resume_id=resume.id,
            job_description_id=job.id,
            generated_content=result["generated_content"],
            ats_score=ats_score,
            match_score=match_score,
            model_used="gpt-4",
            prompt_version="v1",
            temperature=0.3
        )
        
        db.add(variant)
        db.commit()
        db.refresh(variant)
        
        # Embed job for similarity search
        embeddings_service.embed_job_description(
            job_id=job.id,
            job_text=job.raw_text,
            metadata={
                "company": job.company_name,
                "job_title": job.job_title,
                "seniority": job.seniority_level
            }
        )
        
        logger.info(f"✅ Variant generated: {variant.id}")
        
        return {
            "status": "success",
            "variant_id": variant.id,
            "generated_content": variant.generated_content,
            "ats_score": variant.ats_score,
            "match_score": variant.match_score,
            "cached": False,
            "message": "🎉 New tailored resume generated successfully! Download as PDF or DOCX next."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume generation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate resume variant"
        )

# ==================== GENERATE COVER LETTER ====================

@router.post("/cover-letter", summary="Generate cover letter")
async def generate_cover_letter(
    request: GenerateCoverLetterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ✍️ **Generate a personalized cover letter!**
    
    **Requires Authorization**
    
    Uses AI to write a compelling cover letter that:
    - References specific job requirements
    - Shows genuine interest in the company
    - Connects your experience to the role
    - Matches your tone preference
    
    **Tones available:**
    - `professional`: Formal, respectful, achievement-focused
    - `friendly`: Warm, approachable, enthusiastic
    - `assertive`: Confident, direct, impact-focused
    
    **Example request:**
    ```json
    {
        "resume_variant_id": "paste-variant-id-from-generate-resume",
        "job_description_id": "paste-job-id-here",
        "tone": "professional"
    }
    ```
    
    **Steps:**
    1. Generate resume variant first (Generate > resume-variant)
    2. Copy the returned variant_id
    3. Paste it here with job_id
    4. Click Execute!
    """
    
    try:
        # Get resume variant
        variant = db.query(ResumeVariant).filter(
            ResumeVariant.id == request.resume_variant_id
        ).first()
        
        if not variant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume variant not found"
            )
        
        # Verify ownership
        resume = db.query(Resume).filter(
            Resume.id == variant.original_resume_id,
            Resume.user_id == current_user.id
        ).first()
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized - you don't own this variant"
            )
        
        # Get job description
        job = db.query(JobDescription).filter(
            JobDescription.id == request.job_description_id
        ).first()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job description not found"
            )
        
        logger.info(f"Generating cover letter for {job.company_name}")
        
        # Generate cover letter
        cover_letter_text = llm_service.generate_cover_letter(
            user_resume=resume.original_content,
            job_description=job.raw_text,
            company_name=job.company_name or "Company",
            job_title=job.job_title or "Position",
            tone=request.tone
        )
        
        if "Error" in cover_letter_text:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=cover_letter_text
            )
        
        # Store cover letter
        cl = CoverLetter(
            user_id=current_user.id,
            job_description_id=job.id,
            resume_variant_id=variant.id,
            generated_text=cover_letter_text,
            tone=request.tone,
            word_count=len(cover_letter_text.split()),
            model_used="gpt-4"
        )
        
        db.add(cl)
        db.commit()
        db.refresh(cl)
        
        logger.info(f"✅ Cover letter generated: {cl.id}")
        
        return {
            "status": "success",
            "cover_letter_id": cl.id,
            "generated_text": cover_letter_text,
            "tone": request.tone,
            "word_count": cl.word_count,
            "message": "🎉 Cover letter ready! Download as PDF next."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cover letter generation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate cover letter"
        )