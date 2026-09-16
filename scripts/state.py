from typing import TypedDict, List, Optional, Literal

class ProxyState(TypedDict):
    # conversation 
    messages: List[dict]  # full chat history 
    session_id: str       # unique session identifier 

    # user input 
    raw_input: str         # user prompt for failure disc
    failure_type: Optional[str]      # extracted form input
    equipment: Optional[str]         # extracted
    location: Optional[str]
    severity: Optional[str]          # exctracted: low / high / medium / critical

    # retrieval 
    retrieved_handbook: List[str] 
    retrieved_cases: List[str]
    retrived_api: List[str]
    
    # RCA 
    rca_whys: List[str]             # 5 whys method built incrementally
    root_cause: Optional[str]       # final identified root-cause
    rca_confidence: float           # 0.0 - 1.0 
    failure_mode_candidates: List[dict]  # [{"mode": "...", "mechanism": "...", "supporting_symptoms": [...]}]
    confirmed_mechanism: Optional[str]   # single selected machanism causing the failure 
    mechanism_reasoning: Optional[str]   # reason of mechansim selection 

    # clarification
    needs_clarification: bool       # Flag: should we ask the user
    clarification_question: Optional[str] # questions to ask user
    missing_fields: List[str]       # which fields are still unkown

    # output
    solution: Optional[str]         # analysis
    mitigation_plan: Optional[str]  # step-by-step recommendation plan
    response_ready: bool            # Flag: safe to return to frontend

    # FAP 
    case_id: str                     # unique id per project (failure)
    stage: Literal["upload", "ingestion", "synthesis","completeness","mechanism", "5whys", "review", "report", "closed"]   # which stage the case is in 
    dept_files: dict                 # {"maintenance": [], "inspection": [], "engineering": []}
    dept_summaries: dict             # {"maintenance": "...", "inspection": "...", "engineering": "..."}
    unified_context: Optional[str]   # merged synthesis for LLM 
    root_cause_candidates: List[dict] # [{"cause":"...","confidence":0.87}]
    review_decision: Optional[str]   # "accept" | "edit" | "reject"
    review_feedback: Optional[str]   # user edited text or rejection reason
    action_plan: List[str]           # corrective action
    kb_recommendations: List[str]    # from RAG knowledge base
    
    report_ready: bool
    report_content: Optional[str]
    report_path: Optional[str]
