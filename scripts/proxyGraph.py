from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.sqlite import SqliteSaver
from scripts.state import ProxyState

from scripts.nodes.ingestion_node import ingestion_node
from scripts.nodes.synthesis_node import synthesis_node
from scripts.nodes.completness_node import completeness_check_node
from scripts.nodes.failure_mode_node import failure_mode_node
from scripts.nodes.mechanism_node import mechanism_node
from scripts.nodes.rca_whys_node import rca_node
from scripts.nodes.engineer_review_node import engineer_review_node
from scripts.nodes.recommendation_node import recommendation_node
from scripts.nodes.report_node import report_node

import sqlite3

conn = sqlite3.connect("checkpoint.db", check_same_thread=False) # fastAPI handles requests on different threads
checkpointer = SqliteSaver(conn)

graph = StateGraph(ProxyState)

graph.add_node("ingestion", ingestion_node)
graph.add_node("synthesis", synthesis_node)
graph.add_node("completeness_check", completeness_check_node)
graph.add_node("failure_mode", failure_mode_node)
graph.add_node("mechanism", mechanism_node)

graph.add_node("rca", rca_node)
graph.add_node("engineer_review", engineer_review_node)
graph.add_node("recommend", recommendation_node)
graph.add_node("report", report_node)

#graph.set_entry_point("ingestion")  i don't want the graph to always start from here
                                    # sometimes it needs to resume from a certain point 

def route_by_stage(state: ProxyState) -> str:
    stage = state.get("stage", "ingestion")
    routes = {
        "ingestion": "ingestion",
        "failure_mode": "failure_mode",
        "mechanism": "mechanism",
        "rca": "rca",
        "engineer_review": "engineer_review",
        "recommend": "recommend",
        "report": "report",
    }
    return routes.get(stage, "ingestion")


graph.add_conditional_edges(
    START,
    route_by_stage,
    {
        "ingestion": "ingestion",
        "failure_mode": "failure_mode",
        "mechanism": "mechanism",
        "rca": "rca",
        "engineer_review": "engineer_review",
        "recommend": "recommend",
        "report": "report",
    }
)



graph.add_edge("ingestion", "synthesis")
graph.add_edge("synthesis", "completeness_check")

graph.add_conditional_edges(
    "completeness_check",
    lambda state: END if state["needs_clarification"] else "failure_mode", # give control to API if clarification is needed
    {
        END: END,
        "failure_mode": "failure_mode"
    }
)

graph.add_edge("failure_mode", "mechanism")
graph.add_edge("mechanism", "rca")
graph.add_edge("rca", "engineer_review")

graph.add_conditional_edges(
    "engineer_review",
    lambda state: {
        "accept": "recommend",
        "edit": "recommend",
        "reject": "mechanism" if state.get("stage") == "mechanism" else "rca",
        None: END
    }.get(state.get("review_decision")),
    {
        "recommend": "recommend",
        "mechanism": "mechanism",
        "rca": "rca",
        END: END
    }
)


graph.add_edge("recommend", "report")
graph.add_edge("report", END)


app = graph.compile(checkpointer=checkpointer)

