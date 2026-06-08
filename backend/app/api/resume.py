"""
Resume Management Endpoints with Swagger docs
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.models.database import User, Resume, get_db
from app.models.schemas import ResumeUploadRequest, ResumeResponse
from app.api.auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

security = HTTPBearer()

# ==================== UPLOAD RESUME ====================

@router.post("/upload", response_model=ResumeResponse, summary="Upload a resume")
async def upload_resume(
    request: ResumeUploadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and store your resume
    
    **Requires Authorization** - Click Authorize button first!
    
    The resume is parsed and stored as structured JSON for later tailoring.
    
    **Example request:**
    ```json
    {
        "file_name": "my_resume.pdf",
        "file_format": "pdf",
        "content": {
            "name": "John Doe",
            "contact": {
                "email": "john@example.com",
                "phone": "123-456-7890",
                "location": "San Francisco"
            },
            "summary": "5+ years as Senior Python Developer",
            "experience": [
                {
                    "title": "Senior Engineer",
                    "company": "Tech Corp",
                    "duration": {"start": "2020-01-01", "end": "2023-12-31"},
                    "achievements": [
                        "Built scalable microservices with FastAPI",
                        "Led team of 5 engineers",
                        "Reduced API response time by 40%"
                    ]
                }
            ],
            "education": [
                {
                    "degree": "B.S. Computer Science",
                    "school": "MIT",
                    "graduation_year": 2018
                }
            ],
            "skills": {
                "programming": ["Python", "JavaScript", "SQL"],
                "tools": ["Docker", "AWS", "PostgreSQL"]
            }
        }
    }
    ```
    """
    
    try:
        resume = Resume(
            user_id=current_user.id,
            original_content=request.content.model_dump(),
            file_name=request.file_name,
            file_format=request.file_format
        )
        
        db.add(resume)
        db.commit()
        db.refresh(resume)
        
        logger.info(f"✅ Resume uploaded: {resume.id} for user {current_user.email}")
        
        return ResumeResponse(
            id=resume.id,
            user_id=resume.user_id,
            file_name=resume.file_name,
            file_format=resume.file_format,
            created_at=resume.created_at
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Resume upload error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload resume"
        )

# ==================== LIST RESUMES ====================

@router.get("/list", response_model=list[ResumeResponse], summary="List your resumes")
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all your uploaded resumes
    
    **Requires Authorization** - Click Authorize button first!
    """
    
    resumes = db.query(Resume).filter(
        Resume.user_id == current_user.id
    ).order_by(Resume.created_at.desc()).all()
    
    logger.info(f"Listed {len(resumes)} resumes for user {current_user.email}")
    
    return [
        ResumeResponse(
            id=r.id,
            user_id=r.user_id,
            file_name=r.file_name,
            file_format=r.file_format,
            created_at=r.created_at
        )
        for r in resumes
    ]

# ==================== GET RESUME ====================

@router.get("/{resume_id}", response_model=ResumeResponse, summary="Get resume details")
async def get_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific resume with full content
    
    **Requires Authorization**
    
    **Parameters:**
    - resume_id: ID of the resume to retrieve (from /list endpoint)
    """
    
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    return ResumeResponse(
        id=resume.id,
        user_id=resume.user_id,
        file_name=resume.file_name,
        file_format=resume.file_format,
        created_at=resume.created_at
    )

# ==================== DELETE RESUME ====================

@router.delete("/{resume_id}", summary="Delete a resume")
async def delete_resume(
    resume_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a resume
    
    **Requires Authorization**
    
    **Parameters:**
    - resume_id: ID of the resume to delete
    """
    
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    try:
        db.delete(resume)
        db.commit()
        
        logger.info(f"✅ Resume deleted: {resume_id}")
        
        return {"message": "Resume deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Delete error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete resume"
        )