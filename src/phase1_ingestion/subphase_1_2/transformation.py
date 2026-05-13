import json
import os
import logging
from typing import List
from langchain_core.documents import Document

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class DocumentTransformer:
    """
    Handles Phase 1.2: Document Transformation & Chunking.
    Converts cleaned JSON data into LangChain Documents.
    Per Architecture.md, bypasses recursive chunking for document-level embedding.
    """
    
    def __init__(self):
        # Bypassing RecursiveCharacterTextSplitter as per architecture.md
        pass

    def transform(self, input_path: str, output_dir: str = "src/phase1_ingestion/data"):
        """Reads cleaned data and produces document-level chunks."""
        logger.info(f"Starting Phase 1.2: Transformation & Chunking from {input_path}")
        
        if not os.path.exists(input_path):
            logger.error(f"Input file not found: {input_path}")
            return
            
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        with open(input_path, "r", encoding="utf-8") as f:
            funds = json.load(f)

        documents = []
        for fund in funds:
            # Construct content string for embedding
            content = f"Fund Name: {fund['fund_name']}\nNAV: {fund['nav']}\nInvestment Objective: {fund['objective']}"
            
            # Create a base document with full metadata including risk
            doc = Document(
                page_content=content,
                metadata={
                    "source": fund["url"],
                    "fund_name": fund["fund_name"],
                    "risk": fund.get("risk", "N/A"),
                    "version": fund.get("version", "1.1")
                }
            )
            documents.append(doc)

        # Bypass chunking completely. Treat each document as a single chunk.
        chunked_docs = documents
        logger.info(f"Preserved {len(documents)} funds as document-level chunks.")

        # Save chunks for Phase 1.3 (Serialized)
        output_path = os.path.join(output_dir, "chunked_docs.json")
        serialized_chunks = [
            {"page_content": d.page_content, "metadata": d.metadata} 
            for d in chunked_docs
        ]
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(serialized_chunks, f, indent=4)
        
        logger.info(f"Phase 1.2 Complete. Saved chunks to {output_path}")
        return chunked_docs

if __name__ == "__main__":
    transformer = DocumentTransformer()
    transformer.transform("src/phase1_ingestion/data/cleaned_funds.json")
