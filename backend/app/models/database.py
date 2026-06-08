"""
Database Models using SQLAlchemy ORM

WHY SQLALCHEMY:
- ORM = write Python instead of SQL
- Type hints = catch bugs early
- Relationships = handle foreign keys
- Migrations = version control for schema
"""

from sqlalchemy import create_engine, Column, String, DateTime, Text, Float, ForeignKey, ARRAY, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid
import os

# Database URL from environment or default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:saad123@localhost:5432/Smart-resume-maker"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True to see SQL queries
    pool_size=10,
    max_overflow=20
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

# ==================== DATABASE MODELS ====================

class User(Base):
    """
    User Model
    
    WHY THESE FIELDS:
    - id: Unique identifier (UUID better than auto-increment)
    - email: Login credential (unique)
    - name: Display name
    - hashed_password: Never store plain text!
    - created_at/updated_at: Track user lifecycle
    """
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    job_descriptions = relationship("JobDescription", back_populates="user", cascade="all, delete-orphan")
    cover_letters = relationship("CoverLetter", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"


class Resume(Base):
    """
    Original Resume Storage
    
    WHY JSONB FOR CONTENT:
    - Flexible: Different resume formats
    - Queryable: Can search within JSON
    - Versionable: Track changes
    - ML-friendly: Easy feature extraction
    
    STRUCTURE OF original_content:
    {
        "name": "John Doe",
        "contact": {
            "email": "john@example.com",
            "phone": "+1234567890",
            "location": "San Francisco"
        },
        "summary": "Professional summary...",
        "experience": [
            {
                "title": "Senior Engineer",
                "company": "Tech Corp",
                "duration": {"start": "2020-01-01", "end": "2023-12-31"},
                "achievements": ["Achievement 1", "Achievement 2"]
            }
        ],
        "education": [
            {
                "degree": "B.S. Computer Science",
                "school": "MIT",
                "graduation_year": 2020
            }
        ],
        "skills": {
            "programming": ["Python", "JavaScript"],
            "tools": ["Docker", "AWS"]
        }
    }
    """
    __tablename__ = "resumes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Original resume as structured JSON
    original_content = Column(JSON, nullable=False)
    
    # Metadata
    file_name = Column(String(255))
    file_format = Column(String(10))  # 'pdf', 'docx', 'txt'
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="resumes")
    variants = relationship("ResumeVariant", back_populates="original_resume", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Resume(id={self.id}, user_id={self.user_id})>"


class JobDescription(Base):
    """
    Job Description Storage
    
    WHY EXTRACT SKILLS & REQUIREMENTS:
    - Fast filtering (don't re-parse every query)
    - ML features ready (skills, seniority)
    - Historical tracking (trends)
    """
    __tablename__ = "job_descriptions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Raw job posting text
    raw_text = Column(Text, nullable=False)
    
    # Extracted features (for searching and ML)
    extracted_skills = Column(JSON)  # List of skills: ["Python", "FastAPI", "React"]
    extracted_requirements = Column(JSON)  # Structured requirements
    
    # Metadata
    source = Column(String(50))  # 'linkedin', 'indeed', 'company_website'
    source_url = Column(String(500))
    company_name = Column(String(255), index=True)
    job_title = Column(String(255), index=True)
    seniority_level = Column(String(20))  # 'entry', 'mid', 'senior'
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="job_descriptions")
    variants = relationship("ResumeVariant", back_populates="job_description", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<JobDescription(id={self.id}, company={self.company_name}, job={self.job_title})>"


class ResumeVariant(Base):
    """
    AI-Generated Resume Variants
    
    WHY SEPARATE TABLE:
    - Track which variant came from which job + resume
    - Store ML metrics (ats_score, match_score)
    - Enable A/B testing
    - Train future models on feedback
    
    GENERATED_CONTENT STRUCTURE:
    {
        "summary": "Tailored professional summary",
        "experience": [...],
        "skills": ["Python", "FastAPI", ...],
        "ats_optimization_notes": [
            "Added keyword: machine learning",
            "Highlighted leadership experience"
        ]
    }
    """
    __tablename__ = "resume_variants"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    original_resume_id = Column(String, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    job_description_id = Column(String, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # AI-generated content
    generated_content = Column(JSON, nullable=False)
    
    # Quality Metrics (track ML performance for optimization)
    ats_score = Column(Float)  # 0-1: How well it passes ATS
    match_score = Column(Float)  # 0-1: Semantic similarity with job
    keyword_coverage = Column(Float)  # 0-1: % of job keywords in resume
    
    # Generation Details (for reproducibility)
    model_used = Column(String(50))  # 'gpt-4', 'gpt-3.5-turbo'
    prompt_version = Column(String(20))  # Version for reproducibility
    temperature = Column(Float)  # LLM temperature parameter
    generation_time_ms = Column(Float)  # How long it took
    
    # User Feedback (for continuous improvement)
    user_feedback = Column(String(20))  # 'good', 'bad', 'neutral'
    applied = Column(String, default=False)  # Did user apply with this?
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    original_resume = relationship("Resume", back_populates="variants")
    job_description = relationship("JobDescription", back_populates="variants")
    cover_letter = relationship("CoverLetter", back_populates="resume_variant", uselist=False)
    
    def __repr__(self):
        return f"<ResumeVariant(id={self.id}, ats_score={self.ats_score})>"


class CoverLetter(Base):
    """
    Generated Cover Letters
    
    WHY TRACK SEPARATELY:
    - Linked to specific resume variant
    - Track different tones and versions
    - Enable A/B testing of cover letters
    """
    __tablename__ = "cover_letters"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_description_id = Column(String, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_variant_id = Column(String, ForeignKey("resume_variants.id", ondelete="SET NULL"), nullable=True)
    
    # Generated content
    generated_text = Column(Text, nullable=False)
    
    # Metadata
    tone = Column(String(20))  # 'professional', 'friendly', 'assertive'
    word_count = Column(String)
    
    # Generation details
    model_used = Column(String(50))
    generation_time_ms = Column(Float)
    
    # User feedback
    user_feedback = Column(String(20))
    applied = Column(String, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="cover_letters")
    resume_variant = relationship("ResumeVariant", back_populates="cover_letter")
    
    def __repr__(self):
        return f"<CoverLetter(id={self.id}, user_id={self.user_id})>"


# ==================== DATABASE INITIALIZATION ====================

def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created!")


def get_db():
    """
    Dependency for FastAPI to inject database session
    
    WHY:
    - Automatic session management
    - Clean up after request
    - Easy to test with mocks
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_db()