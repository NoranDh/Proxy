# test_rca_whys.py
from scripts.nodes.rca_whys_node import rca_node

state = {
    "unified_context": """
    Maintenance: Centrifugal pump P-101 at Well 4 showed seal leakage.
    Vibration increased over 2 days before failure. Last serviced 3 months ago.
    Inspection: Mechanical seal faces show heat discoloration. O-ring severely degraded.
    Engineering: Process data shows pump ran at 185C for 6 hours, exceeding the 160C
    design limit. Cooling water flow was interrupted at 08:00 on the day of failure.
    Post-maintenance bypass valve position was not verified after last service.
    """,
    "confirmed_mechanism": (
        "Thermal degradation of the mechanical seal caused by cooling water interruption. "
        "The pump exceeded its 160C design limit for 6 hours after the bypass valve was "
        "left open post-maintenance, causing seal face discoloration and O-ring failure."
    ),
    "rca_whys": [],
    "root_cause_candidates": []
}

result = rca_node(state)

print("=" * 60)
print("5 WHYS CHAIN")
print("=" * 60)
for w in result["rca_whys"]:
    print(f"\nWhy {w['level']}: {w['question']}")
    print(f"  → {w['answer']}")

print("\n" + "=" * 60)
print(f"ROOT CAUSE: {result['root_cause']}")
print(f"CONFIDENCE: {result['rca_confidence']}")
print(f"STAGE: {result['stage']}")