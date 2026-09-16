from langchain_openai import ChatOpenAI
from scripts.state import ProxyState
import json

RECOMMENDATION_PROMPT = """
You are a senior reliability engineer at a Saudi Aramco oil and gas facility.
You apply API 571 damage mechanisms and industry best practices.

CONFIRMED ROOT CAUSE:
{root_cause}

5 WHYS ANALYSIS:
{whys_text}

INCIDENT CONTEXT:
{unified_context}

Based on the above, provide:
1. Immediate corrective actions (what to do right now)
2. Short-term recommendations (within 30 days)
3. Long-term prevention measures (inspection intervals, design changes, procedural updates)

Ground your recommendations in API 571 damage mechanisms where applicable.

Respond ONLY with valid JSON, no extra text:
{{
  "kb_recommendations": [
    {{"action": "...", "priority": "immediate|short-term|long-term", "rationale": "..."}}
  ],
  "action_plan": [
    {{"step": 1, "action": "...", "owner": "maintenance|engineering|inspection", "timeline": "..."}}
  ]
}}
"""

def recommendation_node(state: ProxyState) -> dict:
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    root_cause = state.get("root_cause") or state.get("confirmed_mechanism", "Unknown")
    rca_whys = state.get("rca_whys", [])
    unified_context = state.get("unified_context", "")

    whys_text = "\n".join([
        f"Why {w['level']}: {w['question']} → {w['answer']}"
        for w in rca_whys
    ])

    prompt = RECOMMENDATION_PROMPT.format(
        root_cause=root_cause,
        whys_text=whys_text,
        unified_context=unified_context
    )

    resp = llm.invoke([{"role": "user", "content": prompt}])

    try:
        raw = resp.content.strip()
        if "```" in raw:
            parts = raw.split("```")
            raw = parts[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
    except (json.JSONDecodeError, IndexError):
        result = {
            "kb_recommendations": [],
            "action_plan": []
        }

    return {
        "kb_recommendations": result.get("kb_recommendations", []),
        "action_plan": result.get("action_plan", []),
        "stage": "report"
    }