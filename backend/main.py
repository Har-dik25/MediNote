from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tempfile
import os
from typing import Optional

from audio_processor import process_audio
from llm_core import generate_soap_note, extract_clinical_entities
from tools import check_drug_interaction, lookup_guideline, suggest_icd10, lookup_drug_info, suggest_tests
from rag_engine import get_collection_stats, RAG_AVAILABLE

app = FastAPI(
    title="MediMate API",
    description="Backend API for the MediMate Medical Copilot",
    version="1.0.0"
)

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request bodies
class TranscriptRequest(BaseModel):
    transcript: str
    region: Optional[str] = None

class DrugInteractionRequest(BaseModel):
    drug1: str
    drug2: str

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    region: Optional[str] = None

@app.get("/api/health")
async def health_check():
    """Returns the health status of the API and RAG database."""
    stats = get_collection_stats() if RAG_AVAILABLE else {}
    return {
        "status": "healthy",
        "rag_available": RAG_AVAILABLE,
        "collection_stats": stats
    }

@app.post("/api/generate-soap/text")
async def generate_soap_from_text(request: TranscriptRequest):
    """Generates a SOAP note and suggests ICD-10 and tests from a text transcript."""
    if not request.transcript.strip():
        raise HTTPException(status_code=400, detail="Transcript cannot be empty.")
        
    soap_result = generate_soap_note(request.transcript, region=request.region)
    
    print(f"[DEBUG] About to call suggest_icd10, RAG_AVAILABLE={RAG_AVAILABLE}")
    try:
        icd10_suggestions = suggest_icd10(request.transcript, top_k=5)
        print(f"[DEBUG] icd10_suggestions count: {len(icd10_suggestions)}")
    except Exception as e:
        print(f"[DEBUG] suggest_icd10 EXCEPTION: {e}")
        icd10_suggestions = []

    try:
        test_suggestions = suggest_tests(request.transcript, top_k=5, region=request.region)
        print(f"[DEBUG] test_suggestions count: {len(test_suggestions)}")
    except Exception as e:
        print(f"[DEBUG] suggest_tests EXCEPTION: {e}")
        test_suggestions = []
    
    combined_text = f"Transcript:\n{request.transcript}\n\nSOAP Note:\n{soap_result.get('soap_note', '')}"
    try:
        extracted_entities = extract_clinical_entities(combined_text)
        print(f"[DEBUG] extracted_entities: {extracted_entities}")
    except Exception as e:
        print(f"[DEBUG] extract_clinical_entities EXCEPTION: {e}")
        extracted_entities = {"drugs": [], "condition": ""}
    
    return {
        "soap": soap_result,
        "icd10": icd10_suggestions,
        "tests": test_suggestions,
        "extracted_entities": extracted_entities
    }

@app.post("/api/generate-soap/audio")
async def generate_soap_from_audio(file: UploadFile = File(...), region: Optional[str] = Form(None)):
    """Transcribes an audio file and generates a SOAP note."""
    if not file.filename.endswith(('.mp3', '.wav')):
        raise HTTPException(status_code=400, detail="Only .mp3 and .wav files are supported.")
        
    # Save uploaded file to a temporary location
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
            
        # Process audio
        transcript = process_audio(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
            
    soap_result = generate_soap_note(transcript, region=region)
    icd10_suggestions = suggest_icd10(transcript, top_k=5)
    test_suggestions = suggest_tests(transcript, top_k=5, region=region)
    
    combined_text = f"Transcript:\n{transcript}\n\nSOAP Note:\n{soap_result.get('soap_note', '')}"
    extracted_entities = extract_clinical_entities(combined_text)
    
    return {
        "transcript": transcript,
        "soap": soap_result,
        "icd10": icd10_suggestions,
        "tests": test_suggestions,
        "extracted_entities": extracted_entities
    }

@app.post("/api/tools/drug-interaction")
async def check_interaction(request: DrugInteractionRequest):
    """Checks for interactions between two drugs via OpenFDA."""
    result = check_drug_interaction(request.drug1, request.drug2)
    return {"interaction": result}

@app.get("/api/tools/guidelines")
async def get_guidelines(query: str, region: Optional[str] = None):
    """Searches clinical guidelines."""
    result = lookup_guideline(query, region=region)
    return {"result": result}

@app.get("/api/tools/drug-info")
async def get_drug_info(drug_name: str):
    """Looks up drug information from local RAG."""
    result = lookup_drug_info(drug_name)
    return {"result": result}

@app.post("/api/tools/icd10")
async def get_icd10(request: QueryRequest):
    """Suggests ICD-10 codes based on clinical query."""
    result = suggest_icd10(request.query, top_k=request.top_k)
    return {"suggestions": result}

@app.post("/api/tools/tests")
async def get_tests(request: QueryRequest):
    """Suggests diagnostic tests based on clinical query."""
    result = suggest_tests(request.query, top_k=request.top_k)
    return {"suggestions": result}
