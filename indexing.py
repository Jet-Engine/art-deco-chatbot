import time
import os
import logging
import nltk
import sys
import json
from tqdm import tqdm
from file_utils import get_config, read_text, chunk_text_by_sentences
from embeddings import load_embeddings, create_embeddings, generate_embeddings
from pulsejet_rag_client import create_pulsejet_rag_client

# Set up logging
log_filename = 'indexing.log'
logging.basicConfig(level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename=log_filename,
                    filemode='w')

logger = logging.getLogger()

# Silence all other loggers
for log_name, log_obj in logging.Logger.manager.loggerDict.items():
    if isinstance(log_obj, logging.Logger):
        log_obj.setLevel(logging.CRITICAL)

# Redirect stdout to log file
log_file = open(log_filename, 'a')
sys.stdout = log_file

nltk.download('punkt', quiet=True)


def save_metrics(metrics, filepath):
    with open(filepath, 'w') as f:
        json.dump(metrics, f, indent=4)


def main():
    config = get_config()
    logger.info(f"Configuration: {config}")
    pj_rag_client = create_pulsejet_rag_client(config)
    try:
        texts_path = config['rag_files_path']
        embed_model = config['embed_model']
        use_precalculated = config.get('use_precalculated_embeddings', False)

        sentence_per_chunk_val = config.get('sentences_per_chunk', 10)
        overlap_val = config.get('chunk_overlap', 2)
        file_extension = config.get('file_extension', ".txt")

        files_to_process = [f for f in os.listdir(
            texts_path) if f.endswith(file_extension)]
        total_files = len(files_to_process)
        logger.info(f"Total files to process: {total_files}")

        # Restore stdout for tqdm only
        sys.stdout = sys.__stdout__

        metrics = {}

        # Step 1: Load or create embeddings
        print("Step 1: Loading or creating embeddings")
        logger.info("Step 1: Loading or creating embeddings")
        start_time = time.time()
        if use_precalculated:
            print("Using precalculated embeddings")
            logger.info("Using precalculated embeddings")
            embeddings_data = load_embeddings(config)
            if embeddings_data is None:
                raise ValueError(
                    "Failed to load precalculated embeddings. Check the embeddings file path and format.")
        else:
            print("Generating new embeddings")
            logger.info("Generating new embeddings")
            embeddings_data = create_embeddings(
                config, files_to_process, embed_model, sentence_per_chunk_val, overlap_val)
            if embeddings_data is None:
                raise ValueError(
                    "Failed to create new embeddings. Check the embedding creation process.")

        end_time = time.time()
        total_embedding_time = end_time - start_time
        print(
            f"Total embedding {'loading' if use_precalculated else 'generation'} time: {total_embedding_time:.2f} seconds")
        logger.info(
            f"Total embedding {'loading' if use_precalculated else 'generation'} time: {total_embedding_time:.2f} seconds")

        metrics['embedding_time'] = total_embedding_time
        metrics['embedding_method'] = 'loading' if use_precalculated else 'generation'

        # Step 2: Insert embeddings into the vector database
        print("\nStep 2: Inserting embeddings into vector database")
        logger.info("Step 2: Inserting embeddings into vector database")
        start_time = time.time()
        total_vectors = 0

        pj_rag_client.create_collection()
        with tqdm(total=total_files, desc="Inserting Embeddings", unit="file") as pbar:
            for file_name, file_embeddings in embeddings_data.items():
                logger.debug(f"Processing file: {file_name}")
                for chunk_id, content, embed in file_embeddings:
                    metadata = {"filename": file_name,
                                "chunk_id": chunk_id, "content": content}
                    pj_rag_client.insert_vector(embed, metadata)
                    total_vectors += 1
                pbar.update(1)
        end_time = time.time()
        total_insertion_time = end_time - start_time

        print(
            f"Total vector insertion time: {total_insertion_time:.2f} seconds")
        logger.info(
            f"Total vector insertion time: {total_insertion_time:.2f} seconds")

        metrics['insertion_time'] = total_insertion_time
        metrics['total_files'] = total_files
        metrics['total_vectors'] = total_vectors
        metrics['average_insertion_time_per_vector'] = total_insertion_time / \
            total_vectors if total_vectors > 0 else 0

        # Save metrics
        save_metrics(metrics, config['metrics_file_path'])
        logger.info(f"Metrics saved to {config['metrics_file_path']}")

        # Redirect stdout back to log file
        sys.stdout = log_file

        logger.info(
            f"Indexing completed in {total_embedding_time + total_insertion_time:.2f} seconds")

    except Exception as e:
        logger.exception("An error occurred during indexing:")
        # Temporarily restore stdout to print error message
        sys.stdout = sys.__stdout__
        print(
            f"\nAn error occurred during indexing. Check {log_filename} for details.")
        print(f"Error: {str(e)}")
        sys.stdout = log_file
        raise

    finally:
        pj_rag_client.close()
        logger.info("Pulsejet RAG client closed.")
        log_file.close()


if __name__ == "__main__":
    main()
