from scripts.nodes.completness_node import completeness_check_node

thin_state = {
    "unified_context": "A pump failed at well 4.",
    "needs_clarification": False,
    "missing_fields": [],
    "clarification_question": None, 
    "stage": "synthesis"
}

result = completeness_check_node(thin_state)
print("Thin input: ", result)
assert result["needs_clarification"] == True
assert result["clarification_question"] is not None

rich_state = {
    "unified_context": """
    Maintenance: Centrifugal pump P-101 at Well 4 showed seal leakage. 
    Last serviced 3 months ago. Vibration increased over 2 days before failure.
    Inspection: Mechanical seal faces show heat discoloration. O-ring degraded.
    Engineering: Process data shows pump ran at 185°C for 6 hours on the day of failure,
    exceeding the 160°C design limit. Cooling water flow was interrupted at 08:00.
    """,
    "needs_clarification": False,
    "missing_fields": [],
    "clarification_question": None,
    "stage": "synthesis"
}

result = completeness_check_node(rich_state)
print("Rich input:", result)
assert result["needs_clarification"] == False