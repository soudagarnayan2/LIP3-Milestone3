# Phase 2 Edge Cases: RAG Engine

This document identifies potential edge cases during retrieval and answer generation.

| Edge Case | Description | Mitigation Strategy |
|-----------|-------------|---------------------|
| **Irrelevant Queries** | User asks about non-fund topics (e.g., "What is the weather?"). | Implement a classification layer or strict system prompt to refuse non-SBI-MF queries. |
| **Ambiguous Fund Names** | User asks "What are the returns for the Large Cap fund?" when multiple large-cap options exist. | Prompt the user for clarification ("Did you mean SBI Large & Midcap or SBI Bluechip?") or list both. |
| **Empty Retrieval** | No relevant documents are found for a valid query. | Implement a fallback response: "I couldn't find specific details on this in the official docs; please contact customer care." |
| **Hallucination** | LLM generates a plausible but incorrect NAV or percentage. | Use self-consistency checks or secondary "Fact Checker" LLM calls to verify numbers against retrieved context. |
| **Context Overflow** | Too many relevant documents are retrieved, exceeding the LLM's context window. | Implement a reranker (e.g., Cohere) to select only the top 3-5 most relevant chunks. |
