import logging 
from ..schemas import AgentState 
from ..client import LLMClient 

CLIENT = LLMClient()
log = logging.getLogger(__name__) 


REWRITER_PROMPT = """You rewrite user questions into clear, searchable queries
for a financial research system.

Rules:
- Keep the original meaning and any tickers.
- Do not invent or add a company or ticker that is not in the question or history.
- For a general finance concept question, keep the rewrite general and use no ticker.
- Resolve pronouns using the conversation history.
- Expand vague phrases into concrete finance terms.
- Do NOT answer the question. Only rewrite it.
- Return ONE line of plain text, no quotes, no labels.

Examples:
Q: "is it good?" (history: user asked about Apple)
-> Apple AAPL stock investment outlook, valuation, risks and recent performance

Q: "P/E?"
-> explanation of price-to-earnings ratio and how it is used in stock valuation

Q: "compare them" (history: MSFT and GOOGL)
-> compare Microsoft MSFT and Alphabet GOOGL on valuation, growth, and recent news
""" 


def _format_history(history: list[dict], limit: int = 4) -> str:
    if not history:
        return "(none)"
    lines = []
    for turn in history[-limit:]:
        q = turn.get("query", "")
        a = turn.get("answer", "")
        if q:
            lines.append(f"user: {q}")
        if a:
            lines.append(f"assistant: {a[:200]}")
    return "\n".join(lines) or "(none)"



def query_rewrite(state:AgentState): 
    original = state.get("query" , "") 
    intent = state.get("intent", "multi_step")
    tickers = state.get("tickers", []) or []
    history = state.get("history", []) or [] 


    user_block = (
        f"Intent :  {intent}\n" 
        f"known tickers : {tickers}\n" 
        f"History : {_format_history(history)}\n"
        f"Question : {original}\n\n" 
        f"rewrite query"
    ) 

    try: 
        rewritten = CLIENT.generate(messages=[{"role":"system" , "content":REWRITER_PROMPT},
                                            {"role":"user" , "content":user_block}], 
                                            temperature=0.1 , max_tokens=120)  

        print(f"REWRITTEN QUERY : {rewritten}")
        if not rewritten or len(rewritten) < 3:
            rewritten = original

    except Exception as e: 
        log.warning("query rewriter failed, using original: %s", e)
        rewritten = original 

    return {
        "rewritten_query": rewritten,
        "trace": [{
            "node": "query_rewriter",
            "original": original,
            "rewritten": rewritten,
            "intent": intent,
        }],
    }
    
