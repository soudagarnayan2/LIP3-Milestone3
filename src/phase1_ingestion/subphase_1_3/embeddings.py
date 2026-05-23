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

class HFInferenceEmbeddings:
    """
    API-based Hugging Face Embeddings to bypass loading PyTorch/SentenceTransformers locally.
    Uses HF Serverless Inference API. Reduces memory footprint from 550MB to <100MB.
    """
    def __init__(self, model_name: str, hf_token: str):
        self.model_name = model_name
        self.hf_token = hf_token
        self.api_url = f"https://router.huggingface.co/hf-inference/models/{model_name}"
        
    def _embed(self, texts: List[str]) -> List[List[float]]:
        import requests
        headers = {"Authorization": f"Bearer {self.hf_token}"}
        response = requests.post(
            self.api_url,
            headers=headers,
            json={"inputs": texts, "options": {"wait_for_model": True}}
        )
        if response.status_code != 200:
            raise Exception(f"Hugging Face Inference API returned error {response.status_code}: {response.text}")
        
        result = response.json()
        if not isinstance(result, list):
            raise ValueError(f"Unexpected response format from HF: {result}")
            
        # Check if the result is 3D (batch, seq, dim)
        if len(result) > 0 and isinstance(result[0], list) and len(result[0]) > 0 and isinstance(result[0][0], list):
            pooled_result = []
            for doc_tensor in result:
                seq_len = len(doc_tensor)
                dim = len(doc_tensor[0])
                mean_vector = [0.0] * dim
                for token_vector in doc_tensor:
                    for d in range(dim):
                        mean_vector[d] += token_vector[d]
                mean_vector = [val / seq_len for val in mean_vector]
                pooled_result.append(mean_vector)
            return pooled_result
            
        return result
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed(texts)
        
    def embed_query(self, text: str) -> List[float]:
        return self._embed([text])[0]

    def __call__(self, text: str) -> List[float]:
        return self.embed_query(text)

class EmbeddingGenerator:
    """
    Handles Phase 1.3: Vector Embedding Generation using BAAI/bge-small-en-v1.5.
    """
    
    def __init__(self, use_mock: bool = False):
        if use_mock:
            self.embeddings_model = MockEmbeddings()
        else:
            hf_token = os.getenv("HF_TOKEN")
            if hf_token:
                logger.info("Using Hugging Face Inference API for embeddings (low memory mode).")
                self.embeddings_model = HFInferenceEmbeddings(
                    model_name="BAAI/bge-small-en-v1.5", 
                    hf_token=hf_token
                )
            else:
                logger.info("HF_TOKEN not found. Falling back to local HuggingFaceEmbeddings (high memory mode).")
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
