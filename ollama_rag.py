import time

import chromadb
from litellm import completion
from litellm import embedding


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

    query_embed = embedding(model="ollama/" + embed_model, input=query)['data'][0]['embedding']

    rag_start_time = time.time()
    relevant_docs = collection.query(query_embeddings=[query_embed], n_results=5)["documents"][0]
    docs = "\n\n".join(relevant_docs)
    rag_end_time = time.time()

    model_query = f"{query} - Answer that question using the following text as a resource: {docs}"
    response = completion(
        model="ollama/" + main_model,
        messages=[{"role": "user", "content": model_query}],
        api_base="http://localhost:11434"
    ).choices[0].message.content

    end_time = time.time()

    rag_duration = rag_end_time - rag_start_time
    total_duration = end_time - start_time
    llm_duration = total_duration - rag_duration

    return {"response": response, "llm_duration": llm_duration, "rag_duration": rag_duration}


