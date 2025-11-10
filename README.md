# Taller RAG con Solr y Milvus

Este proyecto implementa y compara dos pipelines de **Retrieval-Augmented Generation (RAG)**:
- **Solr (BM25):** recuperación léxica.
- **Milvus (embeddings):** recuperación semántica vectorial.


##  Ejecución con Docker
```bash
docker-compose up --build
```
## Concultas
```bash
curl -X POST "http://localhost:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"query":"¿Qué efectos tuvo el conflicto armado en las mujeres?", "backend":"milvus", "k":5}'
```
##Evaluacion
docker compose run evaluator
