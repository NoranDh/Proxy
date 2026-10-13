from langchain_openai import ChatOpenAI
from scripts.state import ProxyState
import json

MECHANISM_PROMPR = """
You are a senior failure analysis engineer evaluating candidate failure modes
for an industrial incident at a Saudi Arabian oil and gas facility.

Full incident evidence from all three departments:
---
{unified_context}
---

Candidate failure modes under consideration:
---
{candidates}
---

Your task: identify which single failure mode best explains ALL the evidence
simultaneously — maintenance observations, inspection findings, and engineering data.

A valid mechanism must:
- Explain the symptoms reported by ALL three departments, not just one
- Be consistent with the operating conditions described
- Account for the timeline and sequence of events

Evaluate each candidate against the full evidence. Select the one that fits best
and explain specifically why the others are less consistent with this specific incident.

Respond ONLY with valid JSON, no extra text:
{{
  "confirmed_mechanism": "The full mechanism explanation in 2-3 sentences",
  "mode_name": "Short name of the selected mode",
  "reasoning": "Why this mechanism fits all the evidence, and why the others were ruled out",
  "confidence": 0.0
}}
"""

def mechanism_node(state: ProxyState) -> dict:
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    candidates_text = "\n".join(
        f"{i+1}. {c['mode']}: {c['mechanism']}"
        for i, c in enumerate(state.get("failure_mode_candidates", []))
    )

    prompt = MECHANISM_PROMPR.format(
        unified_context = state.get("unified_context", ""),
        candidates = candidates_text
    )

    # engineer rejected the previous analysis: tell the model what to correct
    feedback = state.get("review_feedback")
    if feedback:
        prompt += f"\nThe reviewing engineer rejected the previous analysis with this feedback. Address it:\n{feedback}\n"

    resp = llm.invoke([{"role":"user", "content": prompt}])

    try:
        raw = resp.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())

    except (json.JSONDecodeError, IndexError):
        result = {
            "confirmed_mechanism": "Mechanism selection failed. Manual review required.",
            "mode_name": "Unknown",
            "reasoning": "Parse error",
            "confidence": 0.0

        }

    return {
        "confirmed_mechanism": result.get("confirmed_mechanism"),
        "mechanism_reasoning": result.get("reasoning"),
        "rca_confidence": result.get("confidence", 0.0),
        "stage": "5whys"
    }
