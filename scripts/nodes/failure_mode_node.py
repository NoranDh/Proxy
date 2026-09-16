from langchain_openai import ChatOpenAI
from scripts.state import ProxyState
import json

FAILURE_MODE_PROMPT = """
You are a senior failure analysis engineer with deep expertise in oil and gas equipment
in hydrocarbon processing and production facilities. 

The following incident has been reported and synthesized from three different departments:
---
{unified_context}
---

Using your engineering knowledge of this equipment type, identify 2 to 3 physically
plausible failure modes that could produce the described symptoms.

For each failure mode explain:
- The physical or chemical mechanism that produces these symptoms 
- Which specific symptoms or observations support this mode 

DO NOT reference other incidents or historical cases. 
Reason from the physics, chemistry, and mechanics of this specific equipment type
under the described conditions.

Respond ONLY with a valid JSON array, no extra text:
[
  {{
    "mode": "Short name of the failure mode",
    "mechanism": "The physical/chemical explanation of how this mode produces the observed symptoms",
    "supporting_symptoms": ["symptom 1", "symptom 2"]
  }}
]

"""

def failure_mode_node(state: ProxyState) -> dict:
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    prompt = FAILURE_MODE_PROMPT.format(
        unified_context=state.get("unified_context", "")
    )
    resp = llm.invoke([{"role": "user", "content": prompt}])
    print("RAW RESPONSE:", repr(resp.content[:300]))

    candidates = [{
        "mode": "Unknown failure mode",
        "mechanism": "Could not parse failure modes. Manual review required.",
        "supporting_symptoms": []
    }]

    
    try:
        raw = resp.content.strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        candidates = json.loads(raw)

        if not isinstance(candidates, list):
            candidates = [candidates]
    except (json.JSONDecodeError, IndexError):
        # fallback is already assigned above
        pass
        
    return {
        "failure_mode_candidates": candidates,
        "stage": "mechanism"
    }