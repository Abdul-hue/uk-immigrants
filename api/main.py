import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import session, questions, explain, audit

app = FastAPI(
    title="UK Immigration Eligibility Platform",
    description="Digital Immigration Solicitor — Phase 2",
    version="2.0.0"
)

# CORS configuration
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session.router, prefix="/api/session", tags=["Session"])
app.include_router(questions.router, prefix="/api/questions", tags=["Questions"])
app.include_router(explain.router, prefix="/api/explain", tags=["Explain"])
app.include_router(
    audit.router,
    prefix="/api/audit",
    tags=["Audit"]
)

@app.get("/")
def root():
    return {
        "platform": "UK Immigration Eligibility Platform",
        "phase": "2",
        "status": "running",
        "disclaimer": "This is a Preliminary Self-Assessment only."
    }

@app.get("/health")
def health():
    return {"status": "ok"}
