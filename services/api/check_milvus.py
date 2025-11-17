from pymilvus import connections, list_collections, Collection

connections.connect("default", host="milvus", port="19530")

print("Colecciones disponibles:", list_collections())

if "rag_collection" in list_collections():
    col = Collection("rag_collection")
    print("Número de filas:", col.num_entities)
else:
    print("❌ La colección 'rag_collection' no existe")
