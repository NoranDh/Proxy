from scripts.state import ProxyState
from langchain_openai import ChatOpenAI 
import json

FIVE_WHYS_PROMPT = """
You are a senior failure analysis engineer conducting a 5 Whys root cause analysis
for an industrial incident at a Saudi Arabian oil and gas facility.

Confirmed failure mechanism:
{confirmed_mechanism}

Full incident evidence from all three departments:
{unified_context}

Your task: conduct the complete 5 Whys analysis autonomously.

Rules:
- Start Why 1 from the confirmed mechanism above, not from the symptom
- Each answer must be grounded in the specific conditions, actions, or states
  described in the incident evidence — not general engineering knowledge alone
- Each Why must drill deeper toward a human decision, procedural gap, or
  management system failure that someone could actually fix
- By Why 4 or 5 you should be at a controllable root cause
- Do NOT reference other incidents or use generic answers like "lack of maintenance"
  without specifying what exactly was missed and why

Respond ONLY with valid JSON, no extra text:
{{
  "rca_whys": [
    {{"level": 1, "question": "Why did X happen?", "answer": "Because Y, as evidenced by..."}},
    {{"level": 2, "question": "Why did Y happen?", "answer": "Because Z, which is shown by..."}},
    {{"level": 3, "question": "Why did Z happen?", "answer": "Because..."}},
    {{"level": 4, "question": "Why...?", "answer": "Because..."}},
    {{"level": 5, "question": "Why...?", "answer": "Because..."}}
  ],
  "root_cause": "One clear sentence stating the fundamental controllable cause",
  "confidence": 0.0
}}

"""

def rca_node(state: ProxyState) -> dict:
    llm = ChatOpenAI(model="gpt-4o", temperature=0) # zero creativty to only extract data 
    prompt = FIVE_WHYS_PROMPT.format(
        confirmed_mechanism = state.get("confirmed_mechanism", ""),
        unified_context = state.get("unified_context", "")
    )

    # engineer rejected the previous analysis: tell the model what to correct
    feedback = state.get("review_feedback")
    if feedback:
        prompt += f"\nThe reviewing engineer rejected the previous analysis with this feedback. Address it:\n{feedback}\n"

    result = {
        "rca_whys": [],
        "root_cause": None,
        "rca_confidence": 0.0
    }

    try:
        resp = llm.invoke([{"role": "user", "content": prompt}])
        raw = resp.content.strip()
        if "```" in raw:
            parts = raw.split("```")
            raw = parts[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip())

        result["rca_whys"] = parsed.get("rca_whys", [])
        result["root_cause"] = parsed.get("root_cause")
        result["rca_confidence"] = parsed.get("confidence", 0.0)

    except (json.JSONDecodeError, IndexError, TypeError):
        pass

    result["stage"] = "review"
    return result






