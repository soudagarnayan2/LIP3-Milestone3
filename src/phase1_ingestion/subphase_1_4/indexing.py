import json
import os
import logging
from typing import List, Tuple
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class VectorStoreIndexer:
    """
    Handles Phase 1.4: Vector Store Indexing.
    Loads embedded chunks and initializes a FAISS index with metadata tagging.
    """
    
    def __init__(self, output_dir: str = "src/phase1_ingestion/data/faiss_index"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        # Using HuggingFace BGE model as per Architecture.md (Phase 1.3 / 1.4)
        model_name = "BAAI/bge-small-en-v1.5"
        model_kwargs = {"device": "cpu"}
        encode_kwargs = {"normalize_embeddings": True}
        self.embedding_model = HuggingFaceBgeEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )

    def index(self, input_path: str = "src/phase1_ingestion/data/embedded_chunks.json"):
        """Reads embedded chunks and builds a FAISS index."""
        logger.info(f"Starting Phase 1.4: Vector Store Indexing from {input_path}")
        
        if not os.path.exists(input_path):
            logger.error(f"Input file not found: {input_path}. Please run Phase 1.3 first.")
            return None

        with open(input_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        text_embeddings: List[Tuple[str, List[float]]] = []
        metadatas: List[dict] = []

        for chunk in chunks:
            text = chunk.get("page_content", "")
            embedding = chunk.get("embedding", [])
            
            # Ensure we tag with the mandatory metadata points per Architecture.md
            metadata = {
                "url": chunk.get("metadata", {}).get("source", "N/A"),
                "fund_name": chunk.get("metadata", {}).get("fund_name", "N/A"),
                "risk": chunk.get("metadata", {}).get("risk", "N/A"),
                "version": chunk.get("metadata", {}).get("version", "1.1")
            }
            
            if text and embedding:
                text_embeddings.append((text, embedding))
                metadatas.append(metadata)

        if not text_embeddings:
            logger.error("No valid text/embedding pairs found.")
            return None

        # Build FAISS index from pre-computed embeddings
        logger.info(f"Initializing FAISS index with {len(text_embeddings)} vectors...")
        vector_store = FAISS.from_embeddings(
            text_embeddings,
            embedding=self.embedding_model,
            metadatas=metadatas
        )

        # Save index locally
        vector_store.save_local(self.output_dir)
        logger.info(f"Phase 1.4 Complete. FAISS index saved to {self.output_dir}")
        return vector_store

if __name__ == "__main__":
    indexer = VectorStoreIndexer()
    indexer.index()
