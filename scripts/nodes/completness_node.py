"""
1. What equipment failed and its type/specification
2. The operating environment and conditions at the time
3. The sequence of events or actions that led up to the failure
4. Observable symptoms (what was seen, heard, measured)"""

from langchain_openai import ChatOpenAI
from scripts.state import ProxyState
import json 

COMPLETENESS_PROMPT = """
You are a failure analysis engineer preparing to conduct a 5Whys root cause analysis:
Industrial incident at a Saudi Arabian oil and gas facility.

Before analysis can begin, you need sufficient information in four areas:
1. Equipment — what type of equipment failed and its basic specifications
2. Operating conditions — temperature, pressure, flow rates, or other conditions at the time of failure
3. Event sequence — what actions or events happened leading up to the failure
4. Observable symptoms — what was physically seen, heard, or measured

Below is the synthesized incident report from three departments:
---
{unified_context}
---

Below is the original evidence the report was written from. The report is a summary and
may have left details out, so check here before deciding that something is missing:
---
{evidence}
---

Assess whether the above contains enough information to begin root cause analysis.
Information counts as present if it appears in either the report or the original evidence.

Respond ONLY with valid JSON in this exact format, no extra text:
{{
  "sufficient": true,
  "missing_fields": [],
  "clarification_question": null
}}

OR if information is missing:
{{
  "sufficient": false,
  "missing_fields": ["operating conditions"],
  "clarification_question": "What were the operating temperature and pressure conditions of the pump at the time of failure?"
}}

Rules:
- If insufficient, identify the single most critical missing piece only
- Ask one focused, specific question — not a list
- Do not ask about severity, it can be inferred
- If you have enough to reason about cause and mechanism, set sufficient to true

"""

def completeness_check_node(state: ProxyState) -> dict:
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # the synthesis is a summary, so also show the model what the departments actually submitted
    evidence_parts = [f"Case description: {state.get('raw_input') or 'Not provided'}"]
    for dept, summary in (state.get("dept_summaries") or {}).items():
        evidence_parts.append(f"{dept.capitalize()} department:\n{summary or 'Nothing submitted'}")

    prompt = COMPLETENESS_PROMPT.format(
        unified_context=state.get("unified_context", ""),
        evidence="\n\n".join(evidence_parts)
    )

    resp = llm.invoke([{"role": "user", "content": prompt}])

    # extracting json object from llm response in case llm wraps json

    try:
        raw = resp.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        
    except (json.JSONDecodeError, IndexError):
        # if parsing fails assume sufficient and proceed
        return {
            "needs_clarification": False,
            "missing_fields": [],
            "clarification_question": None, 
            "stage": "5whys"
        }
    
    if result.get("sufficient", False):
        return {
            "needs_clarification": False,
            "missing_fields": [],
            "clarification_question": None, 
            "stage": "5whys"

        }
    
    else:
        return {
            "needs_clarification": True,
            "missing_fields": result.get("missing_fields", []),
            "clarification_question": result.get("clarification_question"),
            "stage": "completeness"

        }