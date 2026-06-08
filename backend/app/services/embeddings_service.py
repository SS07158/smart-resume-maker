"""
Embeddings Service - Using Pinecone Vector Database

Updated with latest langchain-openai imports
"""

import logging
from typing import List, Dict, Optional
import json
from langchain_openai import OpenAIEmbeddings  # UPDATED import
from pinecone import Pinecone
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingsService:
    """Vector embeddings for semantic search"""
    
    def __init__(self):
        """Initialize embeddings and Pinecone"""
        
        logger.info("Initializing Embeddings Service...")
        
        # Initialize OpenAI embeddings
        try:
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=settings.OPENAI_API_KEY
            )
            logger.info("✅ OpenAI Embeddings initialized")
        except Exception as e:
            logger.error(f"Embeddings init error: {str(e)}")
            self.embeddings = None
        
        # Initialize Pinecone
        self.index = None
        try:
            pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            self.index = pc.Index("resume-maker")
            logger.info("✅ Connected to Pinecone index: resume-maker")
        except Exception as e:
            logger.warning(f"⚠️ Pinecone connection error: {str(e)}")
            logger.warning("Embeddings will not be available, but resume generation will still work!")
            self.index = None
    
    def embed_job_description(
        self,
        job_id: str,
        job_text: str,
        metadata: Dict = None
    ) -> bool:
        """Store job description embedding in Pinecone"""
        
        if not self.index or not self.embeddings:
            logger.warning("Pinecone or embeddings not available")
            return False
        
        try:
            logger.info(f"Embedding job: {job_id}")
            
            embedding = self.embeddings.embed_query(job_text)
            
            meta = metadata or {}
            meta["job_text"] = job_text[:1000]
            
            self.index.upsert(
                vectors=[(job_id, embedding, meta)],
                namespace="jobs"
            )
            
            logger.info(f"✅ Job embedded: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Embedding error: {str(e)}")
            return False
    
    def find_similar_jobs(
        self,
        job_text: str,
        top_k: int = 3,
        similarity_threshold: float = 0.85
    ) -> List[Dict]:
        """Find similar job descriptions in vector store"""
        
        if not self.index or not self.embeddings:
            return []
        
        try:
            logger.info("Searching for similar jobs...")
            
            embedding = self.embeddings.embed_query(job_text)
            
            results = self.index.query(
                vector=embedding,
                top_k=top_k,
                namespace="jobs",
                include_metadata=True
            )
            
            similar_jobs = []
            for match in results.get("matches", []):
                similarity = match.get("score", 0)
                
                if similarity >= similarity_threshold:
                    similar_jobs.append({
                        "job_id": match.get("id"),
                        "similarity": similarity,
                        "metadata": match.get("metadata", {})
                    })
            
            logger.info(f"Found {len(similar_jobs)} similar jobs")
            return similar_jobs
            
        except Exception as e:
            logger.error(f"Similarity search error: {str(e)}")
            return []
    
    def embed_resume_section(
        self,
        section_text: str
    ) -> List[float]:
        """Generate embedding for resume section"""
        
        if not self.embeddings:
            return []
        
        try:
            embedding = self.embeddings.embed_query(section_text)
            return embedding
        except Exception as e:
            logger.error(f"Resume embedding error: {str(e)}")
            return []
    
    def calculate_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """Calculate cosine similarity between two texts (0-1)"""
        
        if not self.embeddings:
            return 0.0
        
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            
            emb1 = self.embeddings.embed_query(text1)
            emb2 = self.embeddings.embed_query(text2)
            
            similarity = cosine_similarity(
                [emb1],
                [emb2]
            )[0][0]
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Similarity calculation error: {str(e)}")
            return 0.0