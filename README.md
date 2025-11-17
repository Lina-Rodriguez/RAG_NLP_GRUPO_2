# Taller RAG con Solr y Milvus

Este proyecto implementa y compara dos pipelines de **Retrieval-Augmented Generation (RAG)**:
- **Solr (BM25):** recuperación léxica.
- **Milvus (embeddings):** recuperación semántica vectorial.

##  Ejecución con Docker
```bash
docker-compose up --build
```
## Conexiones creadas para ingresar
- **Solar**
http://solr:8983/solr/rag_collection/select
- **Minvus**
http://milvus:19530/rag_collection
- **API**
http://localhost:8080/docs

Una vez esten funcionales las colecciones se puede ejecutar desde la shell los siguientes comandos

**1.** JSON de la consulta:
```bash
$json = '{ "query": "¿Qué efectos tuvo el conflicto armado en las mujeres?", "backend": "milvus", "k": 5 }'
```
**2.** Invocar la API:
```bash
Invoke-RestMethod -Uri "http://localhost:8000/ask" -Method Post -ContentType "application/json" ` -Body $json
```

