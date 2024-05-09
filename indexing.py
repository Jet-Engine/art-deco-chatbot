import chromadb, time, os, logging
from utilities import read_text, get_config
from mattsollamatools import chunk_text_by_sentences
from tqdm import tqdm
from litellm import embedding
import nltk

nltk.download('punkt')

# Setup logging
log_filename = os.path.splitext(os.path.basename(__file__))[0] + '.log'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_filename),
                        logging.StreamHandler()
                    ])

logger = logging.getLogger()


def create_collection(host, port, collection_name, delete_existing=True):
    client = chromadb.HttpClient(host=host, port=port)
    existing_collections = client.list_collections()
    logger.info(existing_collections)
    # Check if collection exists and delete if specified
    if delete_existing and any(collection.name == collection_name for collection in existing_collections):
        logger.info(f'Deleting collection: {collection_name}')
        client.delete_collection(collection_name)
    # Create or get the collection
    return client.get_or_create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})


def add_text_file_to_collection(collection, file_path, embed_model, sentence_per_chunk_val, overlap_val, pbar):
    filename = os.path.basename(file_path)
    text = read_text(file_path)
    chunks = chunk_text_by_sentences(source_text=text, sentences_per_chunk=sentence_per_chunk_val, overlap=overlap_val)
    pbar.set_description(f"Processing {filename}")
    for index, chunk in enumerate(tqdm(chunks, desc="Chunking", leave=False, position=1)):
        embed = embedding(model="ollama/" + embed_model, input=chunk)['data'][0]['embedding']
        collection.add([filename + str(index)], [embed], documents=[chunk], metadatas={"source": filename})
        pbar.update(1)  # Update the primary progress bar per chunk processed


def main():
    config = get_config()
    collection_name = config['chroma_collection_name']
    texts_path = config['rag_files_path']
    chromadb_host = config['chroma_host']
    chromadb_port = config['chroma_port']
    embed_model = config['embed_model']

    sentence_per_chunk_val = 10
    overlap_val = 2
    file_extension = ".txt"

    # Initialize collection
    collection = create_collection(chromadb_host, chromadb_port, collection_name)

    start_time = time.time()

    # Calculate total chunks to set up the progress bar
    total_chunks = sum(
        len(chunk_text_by_sentences(read_text(os.path.join(texts_path, f)), sentence_per_chunk_val, overlap_val))
        for f in os.listdir(texts_path) if f.endswith(file_extension))

    with tqdm(total=total_chunks, desc="Overall Progress", position=0) as pbar:
        for file_path in [os.path.join(texts_path, f) for f in os.listdir(texts_path) if f.endswith(file_extension)]:
            add_text_file_to_collection(collection, file_path, embed_model, sentence_per_chunk_val, overlap_val, pbar)

    elapsed_time = time.time() - start_time
    logger.info(f"--- {elapsed_time} seconds ---")


if __name__ == "__main__":
    main()
