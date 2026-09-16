from scripts.nodes.failure_mode_node import failure_mode_node
from scripts.nodes.mechanism_node import mechanism_node

test_state = {
    "unified_context": """
    Maintenance: Centrifugal pump P-101 at Well 4 showed seal leakage.
    Vibration increased over 2 days before failure. Last serviced 3 months ago.
    Inspection: Mechanical seal faces show heat discoloration. O-ring severely degraded.
    Engineering: Process data shows pump ran at 185C for 6 hours, exceeding the 160C
    design limit. Cooling water flow was interrupted at 08:00.


""",
"failure_mode_candidates": []
}


# test failure mode node
fm_result = failure_mode_node(test_state)
print("Failure modes found:", len(fm_result["failure_mode_candidates"]))
for m in fm_result["failure_mode_candidates"]:
    print(f" -{m['mode']}: {m['mechanism'][:80]}...")

test_state["failure_mode_candidates"] = fm_result["failure_mode_candidates"]
mech_result = mechanism_node(test_state)
print("\nConfirmed mechanism:", mech_result["confirmed_mechanism"])
print("Confidence:", mech_result["rca_confidence"])