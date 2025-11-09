import os
import pandas as pd
import requests

# URL interna de Solr (desde dentro del contenedor)
SOLR_URL = "http://solr:8983/solr/rag_collection/update?commit=true"

# Nuevas rutas dentro del contenedor (por el volumen montado en docker-compose.yml)
DATA_PATHS = [
    "data/corpus/entrevistas_preprocesado.csv",
    "data/corpus/libro_preprocesado.csv"
]

def index_solr():
    for path in DATA_PATHS:
        if not os.path.exists(path):
            print(f"⚠️  No se encontró el archivo: {path}")
            continue

        print(f"📘 Leyendo dataset: {path}")
        df = pd.read_csv(path)

        docs = []
        for i, row in df.iterrows():
            text = row.get("texto") or row.get("text") or ""
            doc = {
                "id": f"{os.path.basename(path)}_{i}",
                "text": text,
                "source": os.path.basename(path)
            }
            docs.append(doc)

        if not docs:
            print(f"⚠️  No se encontraron documentos en {path}")
            continue

        print(f"🚀 Enviando {len(docs)} documentos a Solr...")
        response = requests.post(SOLR_URL, json=docs)

        if response.status_code == 200:
            print(f"✅ Indexación completada para {path}")
        else:
            print(f"❌ Error al indexar {path}: {response.status_code} - {response.text}")

if __name__ == "__main__":
    index_solr()