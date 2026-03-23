# UK Immigration Eligibility Platform — AI Context

## CRITICAL ARCHITECTURE (Read This First)
This is a DUAL CORPUS system. This is the most important concept.

- Corpus A = Deterministic Rule Engine (PostgreSQL)
  - NEVER uses AI for eligibility decisions
  - Every PASS/FAIL cites a paragraph_ref (e.g. SW-14.1)
  - Source: 45+ GOV.UK appendices scraped and structured as JSON

- Corpus B = Pinecone RAG (explanations ONLY)
  - Model: text-embedding-3-small (1536 dimensions)
  - Index: immigration-corpus-b (28 vectors)
  - NEVER influences eligibility decisions
  - Only explains what rules mean in plain English

## TECH STACK
- Python 3.12.10 (venv312)
- FastAPI (port 8000)
- React + Vite (port 5173)
- PostgreSQL (immigration_db)
- Pinecone (vector store)
- OpenAI gpt-4o (classification + embeddings)
- psycopg2-binary, httpx, BeautifulSoup4

## DATABASE — 11 Tables
- appendices (18 rows) — GOV.UK appendix registry
- rule_paragraphs (128 rows) — raw legal text + constraint_json
- question_templates (123 rows) — user-facing questions, verified=FALSE
- hard_gates (6 rows) — automatic disqualification rules
- rule_change_flags (3 rows) — 2026 law changes
- sessions (27 rows) — user sessions
- session_answers — per-question answers with rule_result
- session_results — final PASS/FAIL/FLAGGED per session
- rule_versions — change history
- scrape_log — scrape audit trail
- assessments — Phase 2 output table

## 2026 RULE CHANGES (Hard-coded, non-negotiable)
1. B2_ENGLISH_UPDATE — Skilled Worker + HPI (from 8 Jan 2026)
2. ETA_MANDATORY — 85 visa-free nations (from 25 Feb 2026)
3. SETTLEMENT_10YR — Most work routes (from April 2026)

## HARD RULES
1. AI never makes eligibility decisions
2. Every decision cites a paragraph_ref
3. question_templates.verified=FALSE until solicitor approves
4. Corpus B never touches Rule Engine
5. All outputs include: "This is a Preliminary Self-Assessment only."

## FOLDER STRUCTURE
- api/ — FastAPI (routers, engine, models)
- api/engine/rule_engine.py — deterministic evaluator (NO AI)
- api/engine/sequence.py — adaptive question sequencer
- classifier/ — GPT-4o intent classifier
- corpus_b/ — Pinecone ingestor + retriever
- hard_gate/ — loader.py + engine.py
- scraper/ — GOV.UK crawler
- extractor/ — GPT-4o rule extractor
- db/ — schema, migrations, connection
- frontend/ — React Vite chat UI
- tests/ — 34 tests, all passing

## CURRENT STATUS
- Phase 1: COMPLETE (scraper, extractor, hard gate, classifier)
- Phase 2: COMPLETE (FastAPI, React, Pinecone, audit trail)
- Phase 3: NOT STARTED (OCR, PDF, Rule Watcher)

## ENVIRONMENT
- Always activate: venv312\Scripts\Activate.ps1
- Start API: python -m uvicorn api.main:app --reload --port 8000 --reload-dir api
- Start UI: cd frontend && npm run dev
- Run tests: python -m pytest tests/ -v