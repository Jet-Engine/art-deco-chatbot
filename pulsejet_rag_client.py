import pulsejet as pj
import logging
from embeddings import get_vector_size

logger = logging.getLogger(__name__)


class PulsejetRagClient:
    def __init__(self, config):
        self.config = config
        self.collection_name = config['pulsejet_collection_name']
        self.main_model = config['main_model']
        self.embed_model = config['embed_model']
        self.client = pj.PulsejetClient(location=config['pulsejet_location'])

    def create_collection(self):
        logger.info(f"Creating collection for RAG using Pulsejet")

        vector_size = get_vector_size(self.config['embed_model'])
        vector_params = pj.VectorParams(
            size=vector_size, index_type=pj.IndexType.HNSW)

        try:
            self.client.create_collection(self.collection_name, vector_params)
            logger.info(f"Created new collection: {self.collection_name}")
        except Exception as e:
            logger.info(
                f"Collection '{self.collection_name}' already exists or error occurred: {str(e)}")

    def insert_vector(self, vector, metadata=None):
        try:
            self.client.insert_single(self.collection_name, vector, metadata)
            logger.debug(f"Inserted vector with metadata: {metadata}")
        except Exception as e:
            logger.error(f"Error inserting vector: {str(e)}")

    def insert_vectors(self, vectors, metadatas=None):
        try:
            self.client.insert_multi(self.collection_name, vectors, metadatas)
            logger.debug(f"Inserted {len(vectors)} vectors")
        except Exception as e:
            logger.error(f"Error inserting multiple vectors: {str(e)}")

    def search_similar_vectors(self, query_vector, limit=5):
        try:
            results = self.client.search_single(
                self.collection_name, query_vector, limit=limit, filter=None)
            return results
        except Exception as e:
            logger.error(f"Error searching for similar vectors: {str(e)}")
            return []

    def get_client_dict(self):
        return {
            'db': self.client,
            'collection': self.collection_name,
            'main_model': self.main_model,
            'embed_model': self.embed_model,
        }

    def close(self):
        try:
            self.client.close()
            logger.info("Closed Pulsejet client connection")
        except Exception as e:
            logger.error(f"Error closing Pulsejet client connection: {str(e)}")


def create_pulsejet_rag_client(config):
    return PulsejetRagClient(config)
