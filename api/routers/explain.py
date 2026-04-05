from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from corpus_b.retriever import explain_paragraph

router = APIRouter()

class ExplainRequest(BaseModel):
    paragraph_ref: str
    question: str

class ExplainResponse(BaseModel):
    paragraph_ref: str
    question: str
    explanation: str
    sources: list[dict]
    disclaimer: str
    corpus_b_status: str

from api.utils import strip_internal_refs

@router.post("/", response_model=ExplainResponse)
def explain_rule(request: ExplainRequest):
    """
    Corpus B endpoint. Explains what an immigration rule means
    in plain English using GOV.UK guidance.
    
    IMPORTANT: This endpoint NEVER changes eligibility results.
    It only provides explanations. The Rule Engine in 
    rule_engine.py is the sole source of pass/fail decisions.
    """
    try:
        result = explain_paragraph(
            paragraph_ref=request.paragraph_ref,
            question=request.question
        )
        # Strip internal refs from the explanation and paragraph_ref in the response
        result["explanation"] = strip_internal_refs(result.get("explanation", ""))
        result["paragraph_ref"] = strip_internal_refs(result.get("paragraph_ref", ""))
        
        return ExplainResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
def explain_health():
    """Check Corpus B connection status."""
    try:
        from corpus_b.retriever import get_index
        index = get_index()
        stats = index.describe_index_stats()
        return {
            "corpus_b": "connected",
            "vector_count": stats.total_vector_count,
            "disclaimer": (
                "Corpus B provides explanations only. "
                "It does not influence eligibility decisions."
            )
        }
    except Exception as e:
        return {
            "corpus_b": "error",
            "detail": str(e)
        }
