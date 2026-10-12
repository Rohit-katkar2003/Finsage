from typing import TypedDict , List , Annotated ,  Literal



import operator 
Intent = Literal["conceptual", "live_data", "document", "multi_step"]
RiskLevel = Literal["conservative", "moderate", "aggressive"]
class AgentState(TypedDict, total=False):
    # ---- input ----
    input_query: str
    query: str                     # sanitized query after guardrails
    rewritten_query: str           # after Query Rewriter

    # ---- session ----
    session_id: str
    user_id: str
    history: Annotated[List[dict], operator.add]
    risk_profile: dict             # {"level": "conservative", "goal": "long-term"}

    # ---- routing ----
    intent: Intent
    tickers: List[str]

    # ---- guardrails ----
    blocked: bool
    block_reason: str

    # ---- tool outputs ----
    market_data: dict          # {ticker: {...}}
    news: List[dict]
    sentiment: dict            # {"overall": "positive", "score": 0.4, "items": [...]}
    metrics: dict              # calculated numbers per ticker

    # ---- generation ----
    answer: str
    citations: List[str]
    confidence: float
    verification: dict         # {"ok": bool, "unsupported": [...], "notes": "..."}
    attempts: int
    
    # ---- control ----
    retries: int
    started_at: float
    trace: Annotated[List[dict], operator.add]
