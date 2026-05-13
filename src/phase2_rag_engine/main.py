import logging
from src.phase2_rag_engine.retriever import HybridRetriever
from src.phase2_rag_engine.generator import RAGGenerator

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_query(query: str):
    logger.info(f"\n--- Processing Query: '{query}' ---")
    
    # Initialize components
    retriever = HybridRetriever()
    generator = RAGGenerator(use_mock=True)
    
    # Step 1: Pre-Retrieval Self-Querying (Metadata Extraction)
    metadata_filters = generator.extract_filters(query)
    
    # Step 2: Metadata-Filtered Hybrid Retrieval
    docs = retriever.retrieve(query, metadata_filters=metadata_filters)
    
    # Step 3: Strict Grounded Generation
    answer, citation = generator.generate_answer(query, docs)
    
    logger.info(f"\nFINAL ANSWER:\n{answer}\n")
    if citation:
        logger.info(f"CITATION: {citation}")

if __name__ == "__main__":
    print("Initializing Phase 2 RAG Pipeline...")
    # Test a query that should trigger metadata filtering
    run_query("What is the NAV of the SBI PSU Fund?")
