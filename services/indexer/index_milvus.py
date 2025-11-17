import os
import pandas as pd
from sentence_transformers import SentenceTransformer
from pymilvus import (
    connections, FieldSchema, CollectionSchema, DataType, Collection, utility
)

MILVUS_HOST = os.getenv("MILVUS_HOST", "milvus")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
COLLECTION_NAME = "rag_collection"

EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EMBED_DIM = 384

# Bajamos el límite de texto para asegurarnos de NO pasar de 5000 “unidades” internas de Milvus
MAX_TEXT_CHARS = 2000
MAX_SOURCE_LEN = 256


def load_texts(path, source_name):
    print(f" Leyendo dataset: {path}")
    if not os.path.exists(path):
        print(f" Archivo no encontrado: {path}")
        return [], []

    df = pd.read_csv(path)

    if "text" not in df.columns:
        print(f" El archivo {path} no tiene columna 'text'")
        return [], []

    # Convertimos a str, quitamos vacíos y TRUNCAMOS FUERTE
    raw_texts = df["text"].fillna("").astype(str).tolist()

    safe_texts = []
    for t in raw_texts:
        t = t.strip()
        if not t:
            continue
        if len(t) > MAX_TEXT_CHARS:
            t = t[:MAX_TEXT_CHARS]
        safe_texts.append(t)

    sources = [source_name[:MAX_SOURCE_LEN]] * len(safe_texts)

    print(f"   {len(safe_texts)} textos válidos")
    if safe_texts:
        max_chars = max(len(t) for t in safe_texts)
        max_bytes = max(len(t.encode("utf-8")) for t in safe_texts)
        print(f"   📏 Máx longitud (chars): {max_chars}, (bytes utf-8): {max_bytes}")

    return safe_texts, sources


def main():
    print(" Conectando a Milvus...")
    connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)

    # Si existe la colección, la borramos
    if utility.has_collection(COLLECTION_NAME):
        print(f"🗑  Borrando colección previa '{COLLECTION_NAME}'...")
        utility.drop_collection(COLLECTION_NAME)

    #  Esquema: mantenemos max_length=5000 pero nuestros textos van a ~2000 chars máx
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=EMBED_DIM),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=5000),
        FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=MAX_SOURCE_LEN),
    ]
    schema = CollectionSchema(fields, description="RAG collection")
    collection = Collection(COLLECTION_NAME, schema)
    print(f" Creada colección '{COLLECTION_NAME}'")

    print(f" Cargando modelo de embeddings ({EMBEDDING_MODEL})...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print(f" Dimensión del embedding: {EMBED_DIM}")

    # Cargar datasets
    textos1, sources1 = load_texts("data/corpus/entrevistas_preprocesado.csv", "entrevista")
    textos2, sources2 = load_texts("data/corpus/libro_preprocesado.csv", "libro")

    all_texts = textos1 + textos2
    all_sources = sources1 + sources2

    if not all_texts:
        print(" No hay textos para indexar, saliendo.")
        return

    # Logueamos tamaño máximo antes de generar embeddings
    max_chars = max(len(t) for t in all_texts)
    max_bytes = max(len(t.encode("utf-8")) for t in all_texts)
    print(f" Global -> Máx longitud (chars): {max_chars}, (bytes utf-8): {max_bytes}")

    print(f" Generando embeddings para {len(all_texts)} textos...")
    embeddings = model.encode(
        all_texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    print(f" Insertando {len(all_texts)} registros en Milvus...")
    mr = collection.insert([embeddings, all_texts, all_sources])
    print(" Insert hecho. Ejemplo de IDs:", mr.primary_keys[:5])

    collection.flush()

    print(" Creando índice sobre 'embedding'...")
    index_params = {
        "metric_type": "IP",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 1024},
    }
    collection.create_index("embedding", index_params)

    print(" Cargando colección en memoria...")
    collection.load()

    print(" Indexación completada.")
    print("Num entidades en colección:", collection.num_entities)


if __name__ == "__main__":
    main()
