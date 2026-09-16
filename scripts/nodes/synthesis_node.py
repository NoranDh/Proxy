from scripts.state import ProxyState
from langchain_openai import ChatOpenAI 


def synthesis_node(state: ProxyState) -> dict:
    llm = ChatOpenAI(model="gpt-4o", temperature=0) # zero creativty to only extract data 

    prompt = f"""You are a failure analysis engineer. Below are findings from three departments
              about the same incident. Synthesise them into a single coherent incident summary, 
              noting agreements and contradictions between departments

              Maintenance: {state['dept_summaries'].get('maintenance','')}
              Inspection: {state['dept_summaries'].get('inspection','')}
              Engineering: {state['dept_summaries'].get('engineering','')}

              Return a structured summary: (1) What failed, (2) Observed conditions,
                                            (3) key evidence from each department, (4) contradictions or gaps. """
    
    resp = llm.invoke([{"role":"user", "content": prompt}])
    return {"unified_context": resp.content, "stage": "5whys"}