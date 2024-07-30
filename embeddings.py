import sys
import os
import time
import io
import logging
import h5py
import numpy as np
import tqdm
from litellm import embedding
from file_utils import read_text, chunk_text_by_sentences

logger = logging.getLogger()


def silent_call(func, *args, **kwargs):
    original_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        result = func(*args, **kwargs)
    finally:
        sys.stdout = original_stdout
    return result


def get_vector_size(embed_model):
    sample_embedding = embedding(
        model="ollama/" + embed_model, input="Sample text")['data'][0]['embedding']
    return len(sample_embedding)


def generate_embeddings(text, embed_model):
    return silent_call(embedding, model="ollama/" + embed_model, input=text)['data'][0]['embedding']


def create_embeddings(config, files_to_process, embed_model, sentence_per_chunk_val, overlap_val):
    embeddings_file = config['embeddings_file_path']
    os.makedirs(os.path.dirname(embeddings_file), exist_ok=True)

    embeddings_data = {}
    start_time = time.time()
    with h5py.File(embeddings_file, 'w') as f:
        for file_name in tqdm(files_to_process, desc="Creating Embeddings", unit="file"):
            file_path = os.path.join(config['rag_files_path'], file_name)
            text = read_text(file_path)
            chunks = silent_call(chunk_text_by_sentences, source_text=text, sentences_per_chunk=sentence_per_chunk_val,
                                 overlap=overlap_val)

            chunk_ids = []
            contents = []
            embeddings = []
            for index, chunk in enumerate(chunks):
                embed = generate_embeddings(chunk, embed_model)
                chunk_ids.append(f"{file_name}_{index}")
                contents.append(chunk)
                embeddings.append(embed)

            file_group = f.create_group(file_name)
            file_group.create_dataset('chunk_ids', data=np.array(
                chunk_ids, dtype=h5py.special_dtype(vlen=str)))
            file_group.create_dataset('contents', data=np.array(
                contents, dtype=h5py.special_dtype(vlen=str)))
            file_group.create_dataset('embeddings', data=np.array(embeddings))

            embeddings_data[file_name] = list(
                zip(chunk_ids, contents, embeddings))

    end_time = time.time()
    embedding_generation_time = end_time - start_time
    logger.info(
        f"Embedding generation took {embedding_generation_time:.2f} seconds")
    return embeddings_data


def load_embeddings(config, file_name=None):
    try:
        embeddings_file = config['embeddings_file_path']
    except TypeError:
        print("Config type:", type(config))
        print("Config contents:", config)
        raise

    if not os.path.exists(embeddings_file):
        raise FileNotFoundError(
            f"Embeddings file not found: {embeddings_file}")

    try:
        with h5py.File(embeddings_file, 'r') as f:
            if file_name:
                # Load embeddings for a single file
                if file_name not in f:
                    logger.warning(
                        f"File '{file_name}' not found in embeddings file. Available files: {list(f.keys())}")
                    return None
                return load_file_embeddings(f[file_name])
            else:
                # Load embeddings for all files
                embeddings_data = {}
                for fname in f.keys():
                    embeddings_data[fname] = load_file_embeddings(f[fname])
                return embeddings_data
    except Exception as e:
        logger.error(f"Error loading embeddings: {str(e)}")
        return None


def load_file_embeddings(file_group):
    chunk_ids = [chunk_id.decode('utf-8')
                 for chunk_id in file_group['chunk_ids'][:]]
    contents = [content.decode('utf-8')
                for content in file_group['contents'][:]]
    embeddings = file_group['embeddings'][:]
    return list(zip(chunk_ids, contents, embeddings))


def insert_embeddings(client, collection_name, file_name, config):
    logger.info(f"Inserting embeddings for file: {file_name}")

    start_time = time.time()
    embeddings_data = load_embeddings(config, file_name)
    end_time = time.time()
    embedding_loading_time = end_time - start_time
    logger.info(
        f"Embedding loading for {file_name} took {embedding_loading_time:.2f} seconds")

    if embeddings_data is None:
        logger.warning(f"Skipping insertion for file: {file_name}")
        return

    start_time = time.time()
    for chunk_id, content, embed in embeddings_data:
        meta = {"filename": file_name,
                "chunk_id": chunk_id, "content": content}
        client.insert_single(collection_name, embed, meta)
    end_time = time.time()
    vector_insertion_time = end_time - start_time

    logger.info(
        f"Vector insertion for {file_name} took {vector_insertion_time:.2f} seconds")
