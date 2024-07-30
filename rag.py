import time
from litellm import completion, embedding
import logging
from pulsejet_rag_client import create_pulsejet_rag_client

logger = logging.getLogger(__name__)


def read_rag_prompt(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip()


def rag(config, query):
    rag_client = create_pulsejet_rag_client(config)
    main_model = config['main_model']
    embed_model = config['embed_model']
    rag_prompt_template = read_rag_prompt(config['rag_prompt_path'])

    start_time = time.time()

    try:
        query_embed = embedding(
            model="ollama/" + embed_model, input=query)['data'][0]['embedding']

        rag_start_time = time.time()
        results = rag_client.search_similar_vectors(query_embed, limit=5)
        rag_end_time = time.time()

        relevant_docs = [result.meta.get('content', '')
                         for result in results.status.element]
        docs = "\n\n".join(relevant_docs)

        model_query = rag_prompt_template.format(query=query, docs=docs)
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
    except Exception as e:
        logger.error(f"Error in RAG process: {e}")
        return {"response": f"An error occurred: {str(e)}", "llm_duration": -1, "rag_duration": -1}
