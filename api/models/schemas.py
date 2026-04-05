from pydantic import BaseModel

class StartSessionRequest(BaseModel):
    user_input: str
    nationality_iso: str

class StartSessionResponse(BaseModel):
    session_id: str
    route: str
    confidence: float
    flags_2026: list[str]
    eta_required: bool
    flag_warnings: list[str]
    next_step: str  # "hard_gate" | "questions" | "needs_clarification"
    hard_gate_questions: list[dict]
    disclaimer: str

class HardGateAnswersRequest(BaseModel):
    session_id: str
    has_deportation_order: bool
    has_used_deception: bool
    has_criminal_conviction: bool
    has_immigration_debt: bool
    has_overstayed_90_days: bool

class HardGateResponse(BaseModel):
    session_id: str
    result: str         # PASS | FLAGGED | HARD_FAIL
    session_can_continue: bool
    flagged_gates: list[dict]
    fail_message: str | None
    next_step: str      # "questions" | "ended" | "solicitor_review"
    disclaimer: str

class NextQuestionResponse(BaseModel):
    session_id: str
    question_number: int
    total_questions: int
    paragraph_ref: str
    ref_id: str  # Technical ID used for submissions, not for rendering
    question_text: str
    answer_type: str
    answer_options: list[str] | None
    heading_context: str | None
    disclaimer: str

class SubmitAnswerRequest(BaseModel):
    session_id: str
    paragraph_ref: str # Kept for backward compatibility, but we should use ref_id
    ref_id: str | None = None
    answer: str

class SubmitAnswerResponse(BaseModel):
    session_id: str
    paragraph_ref: str
    ref_id: str | None = None
    result: str         # PASS | FAIL | FLAG
    fail_reason: str | None
    next_step: str      # "next_question" | "complete"
    disclaimer: str

class CheckSummary(BaseModel):
    question: str
    answer: str
    result: str
    reason: str | None

class SessionResultResponse(BaseModel):
    session_id: str
    overall_result: str
    rules_passed: list[str]
    rules_failed: list[str]
    rules_flagged: list[str]
    summary: list[CheckSummary]
    checklist_items: list[str]
    disclaimer: str
