import fitz
import pandas as pd
from langchain_openai import ChatOpenAI 
from scripts.state import ProxyState

llm = ChatOpenAI(model="gpt-4o", temperature=0) # zero creativty to only extract data 

def ingestion_node(state: ProxyState) -> dict:
    summaries = {}
    for dept, files in state["dept_files"].items():
        dept_text = []
        for f in files: 
            
            if "pdf" in f["content_type"]:
                doc = fitz.open(f["path"])
                text = " ".join(page.get_text() for page in doc)
                dept_text.append(text[:3000])

            elif "image" in f["content_type"]:
                # llm describes image uploded (visible damage)
                resp = llm.invoke([{"role":"user", "content": [
                    {"content_type": "image_url", "image_url":{"url": to_base64(f["path"])}},
                    {"content_type": "text", "text": "Describe all visible damage mechanisms in this failure photo. Be specific about material condition, fracture patterns, corrosion, and wear"}

                ]}])
                dept_text.append(resp.content)
            
            elif "csv" in f["content_type"] or "excel" in f["content_type"]:
                df = pd.read_csv(f["path"])
                dept_text.append(df.describe().to_string())

            elif "text" in f["content_type"]:
                with open(f["path"], "r", encoding="utf-8") as txt:
                    dept_text.append(txt.read())
                    
        summaries[dept] = "\n".join(dept_text)
    return {"dept_summaries": summaries, "stage": "synthesis"}


