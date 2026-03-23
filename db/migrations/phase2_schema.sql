CREATE TABLE IF NOT EXISTS sessions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  route           VARCHAR(50),
  nationality_iso VARCHAR(5),
  flags_2026      JSONB DEFAULT '[]',
  eta_required    BOOLEAN DEFAULT FALSE,
  status          VARCHAR(20) DEFAULT 'active',
  started_at      TIMESTAMP DEFAULT NOW(),
  completed_at    TIMESTAMP,
  disclaimer      TEXT DEFAULT 'This is a Preliminary Self-Assessment only. It does not constitute legal advice. You should consult a qualified immigration solicitor before making any application.'
);

CREATE TABLE IF NOT EXISTS session_answers (
  id              SERIAL PRIMARY KEY,
  session_id      UUID REFERENCES sessions(id),
  paragraph_ref   VARCHAR(30),
  question_text   TEXT,
  answer          TEXT,
  rule_result     VARCHAR(10),
  fail_reason     TEXT,
  answered_at     TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS session_results (
  id              SERIAL PRIMARY KEY,
  session_id      UUID REFERENCES sessions(id) UNIQUE,
  overall_result  VARCHAR(10),
  rules_passed    JSONB DEFAULT '[]',
  rules_failed    JSONB DEFAULT '[]',
  rules_flagged   JSONB DEFAULT '[]',
  checklist_items JSONB DEFAULT '[]',
  disclaimer      TEXT NOT NULL,
  created_at      TIMESTAMP DEFAULT NOW()
);
