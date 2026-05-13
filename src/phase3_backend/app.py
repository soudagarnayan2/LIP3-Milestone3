import re
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Ensure phase 2 modules are accessible
try:
    from src.phase2_rag_engine.retriever import HybridRetriever
    from src.phase2_rag_engine.generator import RAGGenerator
except ImportError:
    pass

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables early
load_dotenv()

from src.phase3_backend.admin import router as admin_router

app = FastAPI(title="SBI Mutual Fund FAQ API", version="1.0")
app.include_router(admin_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG components globally for the API
try:
    retriever = HybridRetriever()
    generator = RAGGenerator(use_mock=False) # Switch to real Groq LLM
except Exception as e:
    logger.error(f"Failed to initialize RAG components: {e}")
    retriever = None
    generator = None

class ChatRequest(BaseModel):
    query: str
    language: str = "en" # 'en' for English, 'hi' for Hindi

class ChatResponse(BaseModel):
    answer: str
    citation_url: Optional[str] = None

def contains_pii(text: str) -> bool:
    """Basic PII check: Looks for common email, phone number, Aadhaar, and PAN patterns."""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'\b\d{10}\b' 
    aadhaar_pattern = r'\b\d{4}\s?\d{4}\s?\d{4}\b' # 12 digit Aadhaar
    pan_pattern = r'\b[A-Z]{5}\d{4}[A-Z]{1}\b' # PAN card
    
    if (re.search(email_pattern, text) or 
        re.search(phone_pattern, text) or 
        re.search(aadhaar_pattern, text) or 
        re.search(pan_pattern, text)):
        return True
    return False

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not retriever or not generator:
        raise HTTPException(status_code=500, detail="RAG Engine not initialized.")

    query = request.query
    logger.info(f"Received query: {query}")

    # Safety Boundary 1: Reject PII
    if contains_pii(query):
        logger.warning("PII detected in query. Rejecting request.")
        raise HTTPException(
            status_code=400, 
            detail="Request rejected: Personal Identifiable Information (PII) detected."
        )

    try:
        # Step 1: Extract Filters
        metadata_filters = generator.extract_filters(query)
        
        # Step 2: Retrieve Documents
        docs = retriever.retrieve(query, metadata_filters=metadata_filters)
        
        # Step 3: Generate Answer (with bilingual support)
        answer, citation_url = generator.generate_answer(query, docs, language=request.language)

        # Safety Boundary 2: Null-Citation for "Don't Know" answers
        fallback_phrases = [
            "i couldn't find", 
            "i don't have that specific information",
            "i'm sorry"
        ]
        
        if any(phrase in answer.lower() for phrase in fallback_phrases):
            logger.info("Answer is a fallback. Stripping citation URL.")
            citation_url = None

        return ChatResponse(answer=answer, citation_url=citation_url)

    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
