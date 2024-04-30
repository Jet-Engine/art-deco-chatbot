import ollama, sys, chromadb

def rag(query, config):
    chroma = chromadb.HttpClient(host=config['chroma_host'], port=config['chroma_port'])
    collection = chroma.get_or_create_collection(config['chroma_collection_name'])

    query_embed = ollama.embeddings(model=config['embed_model'], prompt=query)['embedding']
    relevant_docs = collection.query(query_embeddings=[query_embed], n_results=5)["documents"][0]
    docs = "\n\n".join(relevant_docs)
    model_query = f"{query} - Answer that question using the following text as a resource: {docs}"
    stream = ollama.generate(model=config['main_model'], prompt=model_query, stream=True)
    response = []
    for chunk in stream:
        if chunk["response"]:
            response.append(chunk['response'])
    return ''.join([str(x) for x in response])