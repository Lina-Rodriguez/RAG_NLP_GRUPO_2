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

se debe ver así:
<img width="920" height="618" alt="Captura de pantalla 2025-11-09 122330" src="https://github.com/user-attachments/assets/da7262d1-5ab2-4535-baff-cf3ddbdeb701" />

<img width="920" height="618" alt="Captura de pantalla 2025-11-09 222741" src="https://github.com/user-attachments/assets/d827fc95-48ab-4962-9bd8-54dde1ec2291" />


Una vez esten funcionales las colecciones se puede ejecutar desde la shell los siguientes comandos para realizar consultas:

**1.** JSON de la consulta:
```bash
$json = '{ "query": "¿Qué efectos tuvo el conflicto armado en las mujeres?", "backend": "milvus", "k": 5 }'
```
**2.** Invocar la API:
```bash
Invoke-RestMethod -Uri "http://localhost:8000/ask" -Method Post -ContentType "application/json" ` -Body $json
```

