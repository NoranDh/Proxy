from fastapi import FastAPI, UploadFile, File, Form 
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi import HTTPException
import os
from uuid import uuid4

from scripts.state import ProxyState
from utils.db import save_state, load_state
from scripts.proxyGraph import app as langgraph_app

from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# allowing react frontend to access this API
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# creating a project 
@app.post("/projects")
def create_project(body: dict):
    case_id = str(uuid4())
    initial_state = {
        "case_id": case_id,
        "stage": "upload",
        "dept_files": {"maintenance":[], "inspection":[], "engineering": []},
        "dept_summaries": {},
        "unified_context": None,
        "root_cause_candidates": [],
        "review_decision": None, 
        "review_feedback": None,
        "action_plan": [],
        "kb_recommendations":[],
        "report_ready": False,
        "rca_whys": [],
        "root_cause": None, 
        "message": [],
        "session_id": case_id,
        "raw_input":             body.get("description", ""),
        "failure_type":          None,
        "equipment":             body.get("equipment", None),
        "location":              body.get("location", None),
        "severity":              body.get("severity", None),
        "retrieved_handbook":    [],
        "retrieved_cases":       [],
        "retrieved_aramco":      [],
        "rca_confidence":        0.0,
        "needs_clarification":   False,
        "clarification_question":None,
        "missing_fields":        [],
        "solution":              None,
        "mitigation_plan":       None,
        "response_ready":        False,

    }
    save_state(case_id, initial_state)
    return {"case_id": case_id, "stage":"upload"}

@app.get("/projects/{case_id}")
def get_project(case_id: str):
    state = load_state(case_id)
    return state

@app.post("/projects/{case_id}/upload")
async def upload_file(case_id: str,
                       dept: str = Form(...),
                         file: UploadFile = File(...)):
    
    if dept not in ("maintenance", "inspection", "engineering"):
        return {"error": f"Unknown department: {dept}"}
    
    #save file to disk
    folder = f"uploads/{case_id}/{dept}"
    os.makedirs(folder, exist_ok=True)
    path = f"{folder}/{file.filename}"
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)

    # record action in state 
    state = load_state(case_id)
    state["dept_files"][dept].append({
        "filename": file.filename,
        "path": path, 
        "content_type": file.content_type,
    })
    save_state(case_id, state)
    return {"status": "uploaded", "file": file.filename, "dept": dept}

# connect to run analysis in frontend 
@app.post("/projects/{case_id}/start")
def start_analysis(case_id: str):
    state = load_state(case_id)
    state["stage"] = "ingestion"

    config = {"configurable": {"thread_id": case_id}}
    result = langgraph_app.invoke(state, config=config) # runs langGraph with the state dict untill it hits intrrput or end.
    save_state(case_id, result)
    return {"status": "running",
             "stage": result["stage"],
             "needs_clarification": result.get("needs_clarification", False),
             "clarification_question": result.get("clarification_question"),
            "rca_whys": result.get("rca_whys", [])}

@app.post("/projects/{case_id}/clarify")
def answer_clarification(case_id: str, body: dict):
    
    state = load_state(case_id)

    # append user answer to clarification to unified_context so completeness check sees it
    previous_context = state.get("unified_context", "")
    state["unified_context"] = previous_context + f"\n\nAdditional information: {body['answer']}"

    # reset clarification graph so graph doesn't re-run
    state["needs_clarification"] = False
    state["clarification_question"] = None
    state["missing_fields"] = []
    state["stage"] = "failure_mode"

    save_state(case_id, state)

    config = {"configurable": {"thread_id": case_id}}
    result = langgraph_app.invoke(state, config=config)
    save_state(case_id, result)

    return {
        "stage": result["stage"],
        "needs_clarification": result.get("needs_clarification", False),
        "clarification_question": result.get("clarification_question"),
        "rca_whys": result.get("rca_whys", [])
    }

    
@app.post("/projects/{case_id}/why-answer")
def answer_why(case_id: str, body: dict):
    # body is the json answer sent from frontend for engineer answer 
    # body = {"level": 2, "answer": "Because the heat degree is above average"}

    
    config = {"configurable": {"thread_id": case_id}}
    # load state from db
    state = load_state(case_id) 

    whys = state.get("rca_whys", [])

    # Fill the answer for the waiting Why
    for w in whys:
        if w["level"] == body["level"] and w["answer"] is None:
            w["answer"] = body["answer"]
            break # only update one why at a time

    state["rca_whys"] = whys
    # resume the graph (run rca node again) with new why filled
    save_state(case_id, state)
    langgraph_app.update_state(config, state, as_node="rca") # stateless update
    result = langgraph_app.invoke(None, config=config) # continue the graph with the checkpointer saved state to not overwrite user entry of 5 whys
    save_state(case_id, result)

    return {"stage": result["stage"],
             "rca_whys": result.get("rca_whys", []), 
            "root_cause_candidates": result.get("root_cause_candidates", [])}

@app.post("/projects/{case_id}/review")
def submit_review(case_id: str, body: dict):
    # body = {"decision": "accept"}
    # body = {"decision": "edit", "root_cause": "updated root cause text"}
    # body = {"decision": "reject", "feedback": "the mechanism is wrong"}

    state = load_state(case_id)
    config = {"configurable": {"thread_id": case_id}}

    state["review_decision"]  = body["decision"]
    state["review_feedback"] = body.get("feedback")

    # if engineer edited root cause directly 
    if body["decision"] == "edit" and body.get("root_cause"):
        state["root_cause"] = body ['root_cause']

    save_state(case_id, state)
    langgraph_app.update_state(config, state, as_node="engineer_review")
    result = langgraph_app.invoke(None, config=config)
    save_state(case_id, result)

    return {
        "stage": result["stage"],
        "review_decision": result.get("review_decision"),
        "root_cause_candidates": result.get("root_cause_candidates", []),
        "rca_whys": result.get("rca_whys", []),
        "root_cause": result.get("root_cause")
    }

from fastapi.responses import FileResponse
from fastapi import HTTPException
import os

@app.post("/projects/{case_id}/report")
def generate_report(case_id: str):
    state = load_state(case_id)
    config = {"configurable": {"thread_id": case_id}}

    # Validate 5 Whys
    whys = state.get("rca_whys", [])
    if not whys:
        raise HTTPException(status_code=400, detail="RCA Whys are missing.")
    unanswered = [w for w in whys if isinstance(w, dict) and not w.get("answer")]
    if unanswered:
        raise HTTPException(status_code=400, detail=f"Why level {unanswered[0].get('level')} is unanswered.")

    # Validate mechanism and root cause
    if not state.get("confirmed_mechanism"):
        raise HTTPException(status_code=400, detail="Confirmed mechanism is missing.")
    if not state.get("root_cause"):
        raise HTTPException(status_code=400, detail="Root cause is missing.")

    # fallbacks
    if not state.get("action_plan"):
        state["action_plan"] = ["Not provided"]
    if not state.get("mitigation_plan"):
        state["mitigation_plan"] = "Not provided"
    if not state.get("unified_context"):
        state["unified_context"] = state.get("raw_input", "Not provided")

    save_state(case_id, state)

    state["stage"] = "report"
    result = langgraph_app.invoke(state, config=config)
    save_state(case_id, result)

    # Validate output from result
    report_path = result.get("report_path")
    if not result.get("report_ready"):
        raise HTTPException(status_code=500, detail="Report node did not mark report as ready.")
    if not report_path:
        raise HTTPException(status_code=500, detail="Report node did not return a report path.")
    if not os.path.exists(report_path):
        raise HTTPException(status_code=500, detail=f"Report file not found: {report_path}")

    return FileResponse(
        path=report_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"RCA_Report_{case_id[:8]}.docx",
    )