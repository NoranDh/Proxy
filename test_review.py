# test_review.py
from scripts.nodes.engineer_review_node import engineer_review_node

# Test 1: accept
state = {"review_decision": "accept", "stage": "review", "review_feedback": None}
result = engineer_review_node(state)
assert result["stage"] == "report"
print("Accept:", result)

# Test 2: reject with mechanism feedback
state = {"review_decision": "reject", "stage": "review",
         "review_feedback": "Wrong mechanism, vibration was not the primary cause",
         "rca_whys": [], "root_cause_candidates": []}
result = engineer_review_node(state)
assert result["stage"] == "mechanism"
print("Reject (mechanism):", result)

# Test 3: reject with reasoning feedback  
state = {"review_decision": "reject", "stage": "review",
         "review_feedback": "The reasoning chain skipped the maintenance procedure gap",
         "rca_whys": [], "root_cause_candidates": []}
result = engineer_review_node(state)
assert result["stage"] == "5whys"
print("Reject (5whys):", result)