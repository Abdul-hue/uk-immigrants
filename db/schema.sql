-- UK Immigration Eligibility Platform — Phase 1 Schema

-- 1. appendices
CREATE TABLE IF NOT EXISTS appendices (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    url TEXT,
    priority INT,
    is_hard_gate_source BOOLEAN DEFAULT FALSE,
    flag_2026 VARCHAR(50),
    last_scraped_at TIMESTAMP,
    last_updated_on DATE,
    page_hash VARCHAR(64),
    requires_reverification BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. rule_paragraphs
CREATE TABLE IF NOT EXISTS rule_paragraphs (
    id SERIAL PRIMARY KEY,
    appendix_code VARCHAR(50) REFERENCES appendices(code),
    paragraph_ref VARCHAR(30),
    raw_text TEXT,
    constraint_json JSONB,
    is_hard_gate BOOLEAN DEFAULT FALSE,
    sequence_stage VARCHAR(20),
    requires_human_review BOOLEAN DEFAULT FALSE,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. question_templates
CREATE TABLE IF NOT EXISTS question_templates (
    id SERIAL PRIMARY KEY,
    paragraph_ref VARCHAR(30),
    appendix_code VARCHAR(50),
    sequence_stage VARCHAR(20),
    question_text TEXT,
    answer_type VARCHAR(20),
    answer_options JSONB,
    fail_condition_description TEXT,
    confidence NUMERIC(3,2),
    requires_human_review BOOLEAN DEFAULT FALSE,
    verified BOOLEAN DEFAULT FALSE,
    verified_by VARCHAR(100),
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 4. rule_versions
CREATE TABLE IF NOT EXISTS rule_versions (
    id SERIAL PRIMARY KEY,
    paragraph_ref VARCHAR(30),
    old_text TEXT,
    new_text TEXT,
    old_hash VARCHAR(64),
    new_hash VARCHAR(64),
    detected_at TIMESTAMP DEFAULT NOW()
);

-- 5. scrape_log
CREATE TABLE IF NOT EXISTS scrape_log (
    id SERIAL PRIMARY KEY,
    appendix_code VARCHAR(50),
    run_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20),
    paragraphs_found INT,
    duration_ms INT,
    error_message TEXT
);

-- 6. rule_change_flags
CREATE TABLE IF NOT EXISTS rule_change_flags (
    id SERIAL PRIMARY KEY,
    flag_code VARCHAR(50),
    description TEXT,
    effective_date DATE,
    affected_routes JSONB,
    is_active BOOLEAN DEFAULT TRUE
);

-- Seed rule_change_flags
INSERT INTO rule_change_flags (id, flag_code, description, effective_date, affected_routes, is_active) VALUES
(1, 'B2_ENGLISH_UPDATE', 'English level raised from B1 to B2', '2026-01-08', '["SKILLED_WORKER","HPI"]', TRUE),
(2, 'ETA_MANDATORY', 'ETA required for 85 visa-free nations', '2026-02-25', '["ALL"]', TRUE),
(3, 'SETTLEMENT_10YR', 'Settlement path extended to 10 years', '2026-04-01', '["SKILLED_WORKER","HPI","SCALE_UP"]', TRUE)
ON CONFLICT (id) DO NOTHING;

-- 7. assessments (Phase 2)
CREATE TABLE IF NOT EXISTS assessments (
    id SERIAL PRIMARY KEY,
    session_id UUID,
    appendix_code VARCHAR(50),
    result VARCHAR(10),
    rule_refs_cited JSONB,
    disclaimer_text TEXT DEFAULT 'This is a Preliminary Self-Assessment only. It does not constitute legal advice. You should consult a qualified immigration solicitor before making any application.',
    created_at TIMESTAMP DEFAULT NOW()
);
