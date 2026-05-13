import json
import logging
from typing import List, Dict, Optional
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

class EnsembleRetriever:
    """A lightweight EnsembleRetriever for combining FAISS and BM25 results."""
    def __init__(self, retrievers, weights):
        self.retrievers = retrievers
        self.weights = weights
        
    def invoke(self, query: str):
        all_docs = []
        for r in self.retrievers:
            all_docs.extend(r.invoke(query))
        
        # Deduplicate docs by page_content
        unique_docs = []
        seen_content = set()
        for doc in all_docs:
            if doc.page_content not in seen_content:
                unique_docs.append(doc)
                seen_content.add(doc.page_content)
        return unique_docs
from src.phase1_ingestion.subphase_1_3.embeddings import EmbeddingGenerator

logger = logging.getLogger(__name__)

class HybridRetriever:
    """
    Phase 2: Metadata-Filtered Hybrid Retrieval.
    Combines FAISS semantic search with BM25 keyword search.
    """
    
    def __init__(self, 
                 faiss_index_path: str = "src/phase1_ingestion/data/faiss_index",
                 raw_data_path: str = "src/phase1_ingestion/data/embedded_chunks.json"):
        
        # Load Semantic Retriever
        logger.info(f"Loading FAISS index from {faiss_index_path}")
        self.embeddings = EmbeddingGenerator(use_mock=False).embeddings_model
        try:
            self.faiss_vectorstore = FAISS.load_local(
                faiss_index_path, 
                self.embeddings,
                allow_dangerous_deserialization=True # required for local pickle loading
            )
            # We use k=1 for our Low Top-K strategy
            self.semantic_retriever = self.faiss_vectorstore.as_retriever(search_kwargs={"k": 1})
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            self.faiss_vectorstore = None

        # Load Keyword Retriever
        logger.info(f"Building BM25 Retriever from {raw_data_path}")
        try:
            with open(raw_data_path, "r", encoding="utf-8") as f:
                chunks = json.load(f)
            
            docs = [
                Document(page_content=c["page_content"], metadata=c.get("metadata", {}))
                for c in chunks
            ]
            self.keyword_retriever = BM25Retriever.from_documents(docs)
            self.keyword_retriever.k = 1
        except Exception as e:
            logger.error(f"Failed to build BM25 retriever: {e}")
            self.keyword_retriever = None

        # Combine into Hybrid Retriever (50/50 weighting)
        if self.semantic_retriever and self.keyword_retriever:
            self.ensemble_retriever = EnsembleRetriever(
                retrievers=[self.semantic_retriever, self.keyword_retriever],
                weights=[0.5, 0.5]
            )
        else:
            self.ensemble_retriever = None

    def retrieve(self, query: str, metadata_filters: Optional[Dict] = None) -> List[Document]:
        """
        Retrieves documents using hybrid search, applying metadata filters.
        """
        if not self.ensemble_retriever:
            logger.error("Retrievers not initialized.")
            return []

        logger.info(f"Retrieving context for query: '{query}'")
        
        # If filters are provided, we strictly apply them to the FAISS retriever
        # Note: BM25 in LangChain doesn't natively support pre-filtering easily out of the box,
        # but FAISS does. In a full production build, we'd post-filter BM25 results or use a 
        # vector DB that supports hybrid natively (like Pinecone).
        if metadata_filters and self.faiss_vectorstore:
            logger.info(f"Applying strict metadata filters: {metadata_filters}")
            self.semantic_retriever = self.faiss_vectorstore.as_retriever(
                search_kwargs={"k": 1, "filter": metadata_filters}
            )
            # Rebuild ensemble with the filtered semantic retriever
            self.ensemble_retriever = EnsembleRetriever(
                retrievers=[self.semantic_retriever, self.keyword_retriever],
                weights=[0.5, 0.5]
            )

        docs = self.ensemble_retriever.invoke(query)
        
        # Post-filter docs to ensure absolute strictness across both retrievers
        if metadata_filters:
            filtered_docs = []
            for doc in docs:
                match = True
                for key, val in metadata_filters.items():
                    if doc.metadata.get(key) != val:
                        match = False
                        break
                if match:
                    filtered_docs.append(doc)
            docs = filtered_docs
            
        logger.info(f"Retrieved {len(docs)} highly relevant documents.")
        return docs

if __name__ == "__main__":
    retriever = HybridRetriever()
    # Example usage:
    # docs = retriever.retrieve("What is the NAV?", metadata_filters={"fund_name": "SBI Gold Fund"})
    # print(docs)
