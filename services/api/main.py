from fastapi import FastAPI, Request
from pydantic import BaseModel
import requests
from typing import Optional

app = FastAPI(title="RAG API - Solr vs Milvus")

class QueryRequest(BaseModel):
    query: str
    backend: str  # "solr" or "milvus"
    k: Optional[int] = 5

@app.post("/ask")
async def ask(request: QueryRequest):
    """
    API unificada para consultas RAG
    """
    query = request.query
    backend = request.backend.lower()
    k = request.k

    # Placeholder de búsqueda
    if backend == "solr":
        return {"backend": "solr", "query": query, "results": []}
    elif backend == "milvus":
        return {"backend": "milvus", "query": query, "results": []}
    else:
        return {"error": "Backend inválido. Use 'solr' o 'milvus'."}
