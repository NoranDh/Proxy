from scripts.state import ProxyState

def engineer_review_node(state: ProxyState) -> dict:
    decision = state.get("review_decision")

    if decision == "accept":
        return {"stage": "report"}
    elif decision == "edit":
        # engineer edits root-cause or rca_whys via frontend
        return {"stage": "report"}
    
    elif decision == "reject":
        feedback = state.get("review_feedback", "")

        # Decide where to re-route based on feedback content
        # If feedback suggests the mechanism was wrong -> re-run from mechanism 
        # If feedback suggests the reasoning chain was wrong -> re-run from 5whys

        mechanism_keywords = ["mechanism", "cause", "wrong failure", "not the issue", "misidentified" ]
        feedback_lower = feedback.lower()

        if any(kw in feedback_lower for kw in mechanism_keywords):
            return {
                "stage": "mechanism",
                "rca_whys": [],           # reset the whys chain
                "root_cause_candidates": [],
                "review_decision": None,
            }
        else:
            return {
                "stage": "5whys",
                "rca_whys": [],           # reset the whys chain
                "root_cause_candidates": [],
                "review_decision": None,
            }
    else:
        # no decision yet - wait for engineer response
        from langgraph.types import interrupt
        interrupt("Waiting for engineer review decision")
        return {"stage": "review"}
