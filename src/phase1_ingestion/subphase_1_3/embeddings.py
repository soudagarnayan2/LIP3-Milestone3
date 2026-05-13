import json
import os
import logging
from typing import List, Dict
import numpy as np

# In a real scenario, use: from langchain_openai import OpenAIEmbeddings
# For this demonstration, we'll implement a MockEmbedding to allow Phase 1.3 to run offline.

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class MockEmbeddings:
    """Mock embedding generator for offline testing."""
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        logger.info(f"Generating mock embeddings for {len(texts)} chunks.")
        # Return random vectors of dimension 1536 (standard for text-embedding-3-small)
        return [np.random.rand(1536).tolist() for _ in texts]

class EmbeddingGenerator:
    """
    Handles Phase 1.3: Vector Embedding Generation using BAAI/bge-small-en-v1.5.
    """
    
    def __init__(self, use_mock: bool = False):
        if use_mock:
            self.embeddings_model = MockEmbeddings()
        else:
            from langchain_huggingface import HuggingFaceEmbeddings
            self.embeddings_model = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")

    def generate(self, input_path: str, output_dir: str = "src/phase1_ingestion/data"):
        """Reads chunks and generates embeddings."""
        logger.info(f"Starting Phase 1.3: Embedding Generation from {input_path}")
        
        if not os.path.exists(input_path):
            logger.error(f"Input file not found: {input_path}")
            return

        with open(input_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        texts = [chunk["page_content"] for chunk in chunks]
        
        # Generate embeddings
        vectors = self.embeddings_model.embed_documents(texts)
        
        # Attach vectors to chunks
        for i, chunk in enumerate(chunks):
            chunk["embedding"] = vectors[i]

        # Save embedded chunks for Phase 1.4
        output_path = os.path.join(output_dir, "embedded_chunks.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=4)
        
        logger.info(f"Phase 1.3 Complete. Generated {len(vectors)} embeddings.")
        return chunks

if __name__ == "__main__":
    generator = EmbeddingGenerator(use_mock=False)
    generator.generate("src/phase1_ingestion/data/chunked_docs.json")
