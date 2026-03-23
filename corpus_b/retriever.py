import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv(override=True)

_index = None

def get_query_embedding(text: str) -> list[float]:
    import os, time
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
        timeout=20.0
    )
    return response.data[0].embedding

def get_index():
    global _index
    if _index is None:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        _index = pc.Index(os.getenv("PINECONE_INDEX_NAME", "immigration-corpus-b"))
    return _index

def retrieve_explanation(question: str, paragraph_ref: str = None, top_k: int = 3) -> list[dict]:
    embedding = get_query_embedding(question)
    index = get_index()
    results = index.query(
        vector=embedding,
        top_k=top_k,
        include_metadata=True
    )
    
    matches = []
    for match in results.matches:
        if match.score >= 0.3:
            metadata = match.metadata or {}
            text = metadata.get("text", metadata.get("chunk_index", ""))
            matches.append({
                "text": text,
                "topic": metadata.get("topic", ""),
                "url": metadata.get("url", ""),
                "score": match.score,
                "source": "GOV.UK guidance"
            })
    return matches

def build_explanation(question: str, paragraph_ref: str, chunks: list[dict]) -> str:
    if not chunks:
        return (
            f"No specific guidance found for {paragraph_ref}. "
            "Please refer directly to GOV.UK Immigration Rules "
            "or consult a qualified immigration solicitor."
        )
    
    return f"Based on GOV.UK guidance: {chunks[0]['text'][:500]}\n\nSource: {chunks[0]['url']}"

def explain_paragraph(paragraph_ref: str, question: str) -> dict:
    chunks = retrieve_explanation(question, paragraph_ref)
    explanation_text = build_explanation(question, paragraph_ref, chunks)
    
    return {
        "paragraph_ref": paragraph_ref,
        "question": question,
        "explanation": explanation_text,
        "sources": [
            {"url": c["url"], "topic": c["topic"], "score": c["score"]}
            for c in chunks
        ],
        "disclaimer": (
            "This is a Preliminary Self-Assessment only. "
            "It does not constitute legal advice. "
            "You should consult a qualified immigration "
            "solicitor before making any application."
        ),
        "corpus_b_status": "active"
    }

