cat > docs/ARCHITECTURE.md << 'EOF'
# System Architecture

## 🎓 Why We Designed It This Way

This document explains the architectural decisions. Understanding "why" makes you a great engineer!

## 1. Separation of Concerns

✅ Extension handles UI
✅ FastAPI handles logic  
✅ PostgreSQL handles data
✅ Redis handles caching

This allows each layer to scale independently.

## 2. Async Processing

FastAPI is async-first, so:
- 1000 users can be handled on 1 server
- No blocking I/O
- Horizontal scaling is easy

## 3. Database Design

JSONB fields for resume storage:
- Flexible (different formats)
- Queryable
- ML-friendly
- Versionable

## 4. LLM Integration

LangChain for:
- Prompt version control
- Easy testing
- Cost optimization
- Model swapping

See full details in backend/docs/
EOF