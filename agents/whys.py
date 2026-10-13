from agents import Incident, MechanismsOut, WhysOut
from utils.llm import call_llm
from utils.prompts import WHYS_SYS
import json
from dotenv import load_dotenv
load_dotenv()

def five_whys(case: Incident, mechanisms: MechanismsOut) -> WhysOut:

    prompt = f"""{WHYS_SYS}

Incident:
{case.model_dump()}

Mechanisms (selected, most likely first):
{[m.model_dump() for m in mechanisms.mechanisms]}

Return JSON only."""
    raw = call_llm(prompt, json_expected=True)

    # Robust JSON handling: the 5 Whys are an extra, so never fail the whole analysis
    try:
        return WhysOut(**json.loads(raw))
    except Exception:
        return WhysOut()
