import pandas as pd
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
from sentence_transformers import SentenceTransformer

DATA_PATHS = ["../../data/corpus/entrevistas_preprocesado.csv", "../../data/corpus/libro_preprocesado.csv"]

connections.connect("default", host="milvus", port="19530")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=5000)
]
schema = CollectionSchema(fields, "RAG embeddings")
collection = Collection("rag_collection", schema)

for path in DATA_PATHS:
    df = pd.read_csv(path)
    texts = df["texto"].tolist()
    embeddings = model.encode(texts)
    collection.insert([embeddings, texts])
    collection.flush()

print("✅ Indexación en Milvus completada.")