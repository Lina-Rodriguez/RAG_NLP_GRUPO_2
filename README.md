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
http://localhost:8080/docs**

