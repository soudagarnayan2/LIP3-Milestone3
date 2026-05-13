# Phase 1 Edge Cases: Ingestion & Knowledge Base

This document identifies potential edge cases during document processing and vectorization.

| Edge Case | Description | Mitigation Strategy |
|-----------|-------------|---------------------|
| **Complex Tables** | Financial tables in PDFs span across pages or have nested headers. | Use specialized PDF parsers (like `unstructured` with layout awareness) or convert tables to Markdown/CSV before chunking. |
| **Corrupt PDF Files** | A scheme document is uploaded but is unreadable or password-protected. | Implement pre-ingestion validation checks and automated error reporting for corrupt files. |
| **Chunk Context Loss** | A critical sentence (e.g., "Exit load is 1%") is split between two chunks. | Use overlapping chunks (e.g., 200 token overlap) and semantic chunking boundaries. |
| **Duplicate Documents** | Multiple versions of the same document (e.g., SID vs KIM) are indexed. | Implement hash-based deduplication or metadata-based version control (e.g., `last_updated` field). |
| **Embedding Latency** | High volume of documents causes the embedding API (OpenAI/Gemini) to timeout. | Implement batch processing with retries and exponential backoff. |
