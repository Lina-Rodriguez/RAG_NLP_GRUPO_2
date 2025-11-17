from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, TYPE_CHECKING
import requests
import importlib

# -----------------------------
# Configuración de Solr/Milvus
# -----------------------------
SOLR_SELECT_URL = "http://solr:8983/solr/rag_collection/select"

MILVUS_HOST = "milvus"
MILVUS_PORT = "19530"
MILVUS_COLLECTION_NAME = "rag_collection"

# Milvus opcional
try:
    if TYPE_CHECKING:
        from sentence_transformers import SentenceTransformer  # type: ignore
    else:
        SentenceTransformer = importlib.import_module(
            "sentence_transformers"
        ).SentenceTransformer

    from pymilvus import connections, Collection
    from pymilvus.exceptions import MilvusException

    MILVUS_AVAILABLE = True
except Exception as exc:
    print("Milvus deshabilitado en API:", exc)
    MILVUS_AVAILABLE = False
    MilvusException = Exception  # solo para no romper anotaciones

_milvus_model = None
_milvus_collection = None

app = FastAPI(title="RAG API - Solr vs Milvus")


class QueryRequest(BaseModel):
    query: str
    backend: str  # "solr" o "milvus"
    k: Optional[int] = 5


# -----------------------------
# Utilidades
# -----------------------------
def simplificar_query(q: str) -> str:
    q = q.lower().strip()
    for ch in "¿?¡!,.:":  # limpiamos un poco la pregunta para Solr
        q = q.replace(ch, " ")
    q = " ".join(q.split())
    return q


# -----------------------------
# Búsqueda en Solr
# -----------------------------
def search_solr(query: str, k: int = 5):
    query_clean = simplificar_query(query)

    params = {
        "q": query_clean,
        "defType": "edismax",
        "qf": "text",
        "rows": k,
        "wt": "json",
        "fl": "id,text,source,score",
    }

    try:
        resp = requests.get(SOLR_SELECT_URL, params=params, timeout=10)
        resp.raise_for_status()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error consultando Solr: {exc}")

    data = resp.json()
    docs = data.get("response", {}).get("docs", [])

    results = []
    for d in docs:
        raw_text = d.get("text", "")
        if isinstance(raw_text, list):
            raw_text = " ".join(str(t) for t in raw_text)

        results.append(
            {
                "id": d.get("id"),
                "score": d.get("score", 1.0),
                "text": raw_text,
                "source": d.get("source", "solr"),
            }
        )
    return results


# -----------------------------
# Búsqueda en Milvus
# -----------------------------
def _get_milvus_components():
    """
    Carga perezosa: modelo + conexión + colección.
    Se intenta cargar la colección en memoria, pero si no tiene índice
    y Milvus se queja de 'index not found', seguimos igualmente.
    """
    global _milvus_model, _milvus_collection

    if not MILVUS_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail=(
                "Milvus no está habilitado en el contenedor API. "
                "Instala 'pymilvus' y 'sentence-transformers' en la imagen de api."
            ),
        )

    # Modelo de embeddings
    if _milvus_model is None:
        print("Cargando SentenceTransformer en API...")
        _milvus_model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        print("Modelo cargado en API.")

    # Colección Milvus
    if _milvus_collection is None:
        print("Conectando a Milvus desde API...")
        connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
        col = Collection(MILVUS_COLLECTION_NAME)

        # Intentamos cargar en memoria. Si no tiene índice, Milvus puede lanzar
        # "index not found"; en ese caso seguimos igualmente (búsqueda brute-force).
        try:
            col.load()
        except MilvusException as exc:
            msg = str(exc).lower()
            if "index not found" in msg:
                print(
                    f" Colección '{MILVUS_COLLECTION_NAME}' sin índice en Milvus; "
                    "se usará búsqueda directa sin índice."
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"Error cargando la colección '{MILVUS_COLLECTION_NAME}' "
                        f"en Milvus: {exc}"
                    ),
                )

        print(
            f" Colección '{MILVUS_COLLECTION_NAME}' preparada, "
            f"{col.num_entities} entidades."
        )
        _milvus_collection = col

    return _milvus_model, _milvus_collection


def search_milvus(query: str, k: int = 5):
    model, collection = _get_milvus_components()

    # Si no hay nada en la colección, devolvemos vacío
    if collection.num_entities == 0:
        return []

    # 1) Embedding de la pregunta
    # IMPORTANTE: si en el indexer usas normalize_embeddings=True,
    # pon lo mismo aquí para mantener coherencia.
    query_vec = model.encode([query]).tolist()  # -> [[dim]]

    # 2) Parámetros de búsqueda: IP para coincidir con el índice
    search_params = {
        "metric_type": "IP",
        "params": {"nprobe": 10},
    }

    # Por si la colección se ha "descargado" del QueryNode, intentamos load de nuevo
    try:
        collection.load()
    except MilvusException as exc:
        msg = str(exc).lower()
        if "index not found" in msg:
            print(
                f" Colección '{MILVUS_COLLECTION_NAME}' sin índice al hacer search; "
                "se sigue con búsqueda directa."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Error cargando la colección en Milvus: {exc}",
            )

    try:
        res = collection.search(
            data=query_vec,
            anns_field="embedding",      # nombre del campo vectorial
            param=search_params,
            limit=k,
            output_fields=["text", "source"],  # pedimos también 'source'
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error consultando Milvus: {exc}")

    hits = res[0] if res else []

    results = []
    for hit in hits:
        ent = hit.entity

        # Text
        text_value = ""
        try:
            text_value = ent.get("text", "")
        except Exception:
            try:
                text_value = ent["text"]
            except Exception:
                text_value = getattr(ent, "text", "")

        # Source
        source_value = "milvus"
        try:
            source_value = ent.get("source", "milvus")
        except Exception:
            try:
                source_value = ent["source"]
            except Exception:
                source_value = getattr(ent, "source", "milvus")

        results.append(
            {
                "id": hit.id,
                # Para IP: a mayor distance, más similar (lo dejamos tal cual)
                "score": float(hit.distance),
                "text": text_value,
                "source": source_value,
            }
        )

    return results


# -----------------------------
# Endpoints
# -----------------------------
@app.get("/")
async def root():
    return {"status": "ok", "message": "RAG API Solr/Milvus en funcionamiento"}


@app.post("/ask")
async def ask(request: QueryRequest):
    query = request.query
    backend = request.backend.lower()
    k = request.k or 5

    if backend == "solr":
        results = search_solr(query, k)
        return {"backend": "solr", "query": query, "k": k, "results": results}

    elif backend == "milvus":
        results = search_milvus(query, k)
        return {"backend": "milvus", "query": query, "k": k, "results": results}

    else:
        raise HTTPException(
            status_code=400,
            detail="Backend inválido. Use 'solr' o 'milvus'.",
        )
