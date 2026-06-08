"""
Pydantic Schemas for API requests/responses

WHY PYDANTIC:
- Data validation at API boundary
- Type hints = IDE autocomplete
- Automatic JSON schema generation
- Clear API contracts
"""

from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# ==================== USER SCHEMAS ====================

class UserRegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2)

class UserLoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserResponse(BaseModel):
    """User response (no password)"""
    id: str
    email: str
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==================== RESUME SCHEMAS ====================

class ResumeContactInfo(BaseModel):
    """Contact information in resume"""
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None

class ResumeExperience(BaseModel):
    """Work experience"""
    title: str
    company: str
    duration: Optional[Dict[str, str]] = None
    achievements: List[str] = []

class ResumeEducation(BaseModel):
    """Education"""
    degree: str
    school: str
    graduation_year: Optional[int] = None

class ResumeSkills(BaseModel):
    """Skills grouped by category"""
    programming: List[str] = []
    tools: List[str] = []
    soft_skills: List[str] = []

class ResumeContent(BaseModel):
    """Full resume content"""
    name: str
    contact: ResumeContactInfo
    summary: Optional[str] = None
    experience: List[ResumeExperience] = []
    education: List[ResumeEducation] = []
    skills: Dict[str, List[str]] = {}

class ResumeUploadRequest(BaseModel):
    """Resume upload request"""
    file_name: str
    file_format: str  # 'pdf', 'docx', 'txt'
    content: ResumeContent

class ResumeResponse(BaseModel):
    """Resume response"""
    id: str
    user_id: str
    file_name: str
    file_format: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==================== JOB DESCRIPTION SCHEMAS ====================

class JobDescriptionRequest(BaseModel):
    """Submit job description"""
    raw_text: str
    source: Optional[str] = None
    source_url: Optional[str] = None

class JobDescriptionResponse(BaseModel):
    """Job description response"""
    id: str
    company_name: Optional[str]
    job_title: Optional[str]
    seniority_level: Optional[str]
    extracted_skills: Optional[List[str]]
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==================== GENERATION SCHEMAS ====================

class GenerateResumeVariantRequest(BaseModel):
    """Request to generate resume variant"""
    resume_id: str
    job_description_id: str
    user_preferences: Dict[str, Any] = {}

class GenerateResumeVariantResponse(BaseModel):
    """Resume variant response"""
    id: str
    variant_id: str
    generated_content: Dict[str, Any]
    ats_score: Optional[float]
    match_score: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True

class GenerateCoverLetterRequest(BaseModel):
    """Request to generate cover letter"""
    resume_variant_id: str
    job_description_id: str
    tone: str = Field(default="professional", pattern="^(professional|friendly|assertive)$")

class CoverLetterResponse(BaseModel):
    """Cover letter response"""
    id: str
    generated_text: str
    tone: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==================== HEALTH CHECK ====================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)