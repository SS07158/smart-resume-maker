"""
Job Description Endpoints with Swagger docs
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database import User, JobDescription, get_db
from app.models.schemas import JobDescriptionRequest, JobDescriptionResponse
from app.api.auth import get_current_user
from app.services.job_parser import JobDescriptionExtractor
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# ==================== SUBMIT JOB DESCRIPTION ====================

@router.post("/", response_model=JobDescriptionResponse, summary="Submit a job description")
async def create_job_description(
    request: JobDescriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a job posting to analyze
    
    **Requires Authorization** - Click Authorize button first!
    
    The system will automatically:
    - Extract key skills
    - Determine seniority level
    - Extract requirements
    - Prepare for resume generation
    
    **Example request:**
    ```json
    {
        "raw_text": "Senior Python Developer at TechCorp\n\nRequirements:\n- 5+ years Python experience\n- FastAPI or Django expertise\n- PostgreSQL and MongoDB\n- Docker and Kubernetes\n- AWS cloud experience\n\nResponsibilities:\n- Build scalable APIs\n- Lead technical decisions\n- Mentor junior developers",
        "source": "linkedin",
        "source_url": "https://linkedin.com/jobs/123"
    }
    ```
    """
    
    try:
        # Extract job features
        extractor = JobDescriptionExtractor()
        skills = extractor.extract_skills(request.raw_text)
        requirements = extractor.extract_requirements(request.raw_text)
        seniority = extractor.extract_seniority_level(request.raw_text)
        company_info = extractor.extract_company_info(request.raw_text)
        
        # Create job description record
        job = JobDescription(
            user_id=current_user.id,
            raw_text=request.raw_text,
            extracted_skills=skills,
            extracted_requirements=requirements,
            source=request.source,
            source_url=request.source_url,
            company_name=company_info.get("company_name"),
            job_title=company_info.get("job_title"),
            seniority_level=seniority
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        
        logger.info(f"✅ Job description created: {job.id}")
        logger.info(f"   Seniority: {job.seniority_level}")
        logger.info(f"   Skills found: {', '.join(skills[:5])}")
        
        return JobDescriptionResponse(
            id=job.id,
            company_name=job.company_name,
            job_title=job.job_title,
            seniority_level=job.seniority_level,
            extracted_skills=job.extracted_skills,
            created_at=job.created_at
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Job description error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process job description"
        )

# ==================== LIST JOB DESCRIPTIONS ====================

@router.get("/list", response_model=list[JobDescriptionResponse], summary="List your job descriptions")
async def list_job_descriptions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all job postings you've submitted
    
    **Requires Authorization**
    """
    
    jobs = db.query(JobDescription).filter(
        JobDescription.user_id == current_user.id
    ).order_by(JobDescription.created_at.desc()).all()
    
    return [
        JobDescriptionResponse(
            id=j.id,
            company_name=j.company_name,
            job_title=j.job_title,
            seniority_level=j.seniority_level,
            extracted_skills=j.extracted_skills,
            created_at=j.created_at
        )
        for j in jobs
    ]

# ==================== GET JOB DESCRIPTION ====================

@router.get("/{job_id}", response_model=JobDescriptionResponse, summary="Get job description details")
async def get_job_description(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific job description with extracted features
    
    **Requires Authorization**
    
    **Parameters:**
    - job_id: ID of the job description (from /list endpoint)
    """
    
    job = db.query(JobDescription).filter(
        JobDescription.id == job_id,
        JobDescription.user_id == current_user.id
    ).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found"
        )
    
    return JobDescriptionResponse(
        id=job.id,
        company_name=job.company_name,
        job_title=job.job_title,
        seniority_level=job.seniority_level,
        extracted_skills=job.extracted_skills,
        created_at=job.created_at
    )