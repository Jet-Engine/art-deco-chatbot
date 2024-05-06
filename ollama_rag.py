import time

import ollama, sys, chromadb


def create_client(config):
    host = config['chroma_host']
    port = config['chroma_port']
    collection = config['chroma_collection_name']
    chroma = chromadb.HttpClient(host=host, port=port)
    collection = chroma.get_or_create_collection(collection)

    main_model = config['main_model']
    embed_model = config['embed_model']
    return {'db': chroma, 'collection': collection, 'main_model': main_model, 'embed_model': embed_model}


def rag(client, query):
    collection = client['collection']
    main_model = client['main_model']
    embed_model = client['embed_model']

    start_time = time.time()
    query_embed = ollama.embeddings(embed_model, prompt=query)['embedding']

    rag_start_time = time.time()
    relevant_docs = collection.query(query_embeddings=[query_embed], n_results=5)["documents"][0]
    rag_end_time = time.time()

    docs = "\n\n".join(relevant_docs)
    model_query = f"{query} - Answer that question using the following text as a resource: {docs}"
    stream = ollama.generate(main_model, prompt=model_query, stream=True)
    end_time = time.time()

    rag_duration = rag_end_time - rag_start_time
    total_duration = end_time - start_time
    llm_duration = total_duration - rag_duration

    response = []
    for chunk in stream:
        if chunk["response"]:
            response.append(chunk['response'])
    response = ''.join([str(x) for x in response])
    return {"response": response, "llm_duration": llm_duration, "rag_duration": rag_duration}
