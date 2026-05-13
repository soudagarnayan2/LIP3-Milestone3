# SBI Mutual Fund FAQ Chatbot — Problem Statement

> **Project Code**: LIP3 | **Domain**: FinTech / Conversational AI | **Organization**: SBI Mutual Fund

---

## 1. Executive Summary

SBI Mutual Fund is one of India's largest asset management companies, managing thousands of crores in Assets Under Management (AUM) across a wide portfolio of equity, debt, hybrid, and thematic funds. Despite a robust product offering, a significant friction point exists in the customer journey: **investors and advisors routinely struggle to find accurate, contextual, and timely answers to fund-related queries**.

This project proposes the design and development of an **AI-powered FAQ Chatbot** — an intelligent conversational assistant capable of answering natural language questions about SBI Mutual Fund products, policies, NAV, SIP terms, KYC processes, and regulatory guidelines. The system will drastically reduce the support burden on human agents while delivering an instant, accurate, and 24×7 accessible knowledge experience for end users.

---

## 2. Background & Context

### 2.1 Industry Landscape

The Indian mutual fund industry has witnessed unprecedented growth, with retail participation surging through digital channels. However, as the investor base broadens — especially into Tier 2 and Tier 3 cities — the diversity of questions grows exponentially:

- New investors asking fundamental onboarding questions ("What is an NFO?", "How do I start a SIP?")
- Existing investors seeking fund-specific details ("What is the exit load for SBI Bluechip Fund?")
- Financial advisors needing granular regulatory or factsheet information in real time

### 2.2 Existing Limitations

| Pain Point | Current State | Impact |
|---|---|---|
| **Static FAQ Pages** | Flat, unstructured HTML pages with no search | Users leave without answers |
| **Customer Support Agents** | High call/chat volumes; long wait times | Poor CSAT scores |
| **Fund Factsheets (PDFs)** | Information locked inside unindexed PDFs | Hard to discover at point of need |
| **Regulatory Updates** | Manually updated; often outdated | Risk of misinformation |
| **Multilingual Needs** | Predominantly English only | Excludes non-English-speaking investors |

### 2.3 Opportunity

A Retrieval-Augmented Generation (RAG) based chatbot can bridge this gap by:
- **Ingesting** structured and unstructured knowledge sources (FAQs, factsheets, SEBI circulars, scheme documents)
- **Retrieving** the most semantically relevant chunks for any user query
- **Generating** accurate, grounded, human-readable answers using a Large Language Model (LLM)

---

## 3. Problem Statement

> **How can we build a scalable, accurate, and contextually intelligent FAQ chatbot for SBI Mutual Fund that enables investors, financial advisors, and customer support staff to instantly retrieve reliable answers from a heterogeneous knowledge base — without requiring human intervention for routine queries?**

### 3.1 Core Challenges

1. **Heterogeneous Knowledge Sources**: Fund data exists across PDFs, websites, Excel sheets, and internal databases — each with different structure, format, and update frequency.

2. **Semantic Gap**: Traditional keyword search fails for natural language queries like *"Is this fund suitable for a conservative investor with a 3-year horizon?"* — requiring true semantic understanding.

3. **Hallucination Risk**: General-purpose LLMs may fabricate fund-specific data (NAV, returns, AUM). The system must ground every response strictly in verified source documents.

4. **Freshness & Accuracy**: NAV, portfolio allocations, and regulatory guidelines change frequently. The knowledge base must support incremental, real-time updates without full re-indexing.

5. **Multi-turn Dialogue**: Users often ask follow-up questions in conversation context ("Which of the two is better for my goal?"). The system must maintain session-aware dialogue state.

6. **Scale & Latency**: The system must serve thousands of concurrent users with sub-3-second response times at production scale.

7. **Explainability & Trust**: For financial queries, users must trust the source. Every answer should cite the originating document/section to build credibility.

8. **Accessibility**: The system should support multiple input modes (text, voice) and ideally bilingual interaction (English + Hindi) to maximize reach.

---

## 4. Objectives

| # | Objective | Success Metric |
|---|---|---|
| O1 | Accurate FAQ resolution without hallucination | ≥ 90% factual accuracy on benchmark test set |
| O2 | Sub-3-second end-to-end response time | P95 latency < 3s under load |
| O3 | Reduce customer support ticket volume | ≥ 40% deflection rate within 3 months |
| O4 | Multi-turn conversational ability | BLEU / BERTScore evaluation on dialogue benchmarks |
| O5 | Source-cited answers | 100% of responses include document citation |
| O6 | Live knowledge base update | < 15 minutes from document upload to query-ready |
| O7 | Scalability | Handles 500 concurrent users on standard cloud infra |

---

## 5. Scope

### In Scope
- **Exclusive Data Sourcing**: Ingestion strictly limited to the 9 identified SBI Mutual Fund product URLs from Groww.in (no external web crawling).
- FAQ ingestion and embedding pipeline (PDF, HTML, CSV sources)
- Vector database for semantic search
- LLM-powered answer generation with RAG
- RESTful API backend (FastAPI)
- Web-based chat UI (Next.js / React)
- Admin panel for document management and analytics
- Conversation history and session management
- Source citation in responses
- Evaluation pipeline (automated + human)

### Out of Scope (v1.0)
- Real-time NAV feed integration (planned for v2.0)
- Voice interface / IVR integration
- Full Hindi NLP support (pilot only)
- Integration with SBI core banking systems
- Regulatory compliance workflow automation

---

## 6. Stakeholders

| Stakeholder | Role | Interest |
|---|---|---|
| **Retail Investors** | Primary End Users | Fast, accurate, trustworthy answers |
| **Financial Advisors (MFDs/RIAs)** | Power Users | Deep fund-specific data on demand |
| **Customer Support Team** | Internal Users | Reduced inbound ticket volume |
| **Compliance / Legal** | Governance | Grounded responses, no misinformation |
| **IT / Engineering** | System Owners | Maintainability, scalability, security |
| **Business / Marketing** | Sponsors | User engagement, lead generation |

---

## 7. Constraints & Assumptions

### Constraints
- All LLM responses must be grounded in SBI MF's own knowledge base — no external web browsing
- System must comply with SEBI communication guidelines
- PII (e.g., PAN, Aadhaar) must never be requested or stored by the chatbot
- Deployment to be on cloud infrastructure (AWS / Azure / GCP)

### Assumptions
- A curated set of FAQ documents, scheme information documents (SID), and key information memoranda (KIM) will be provided by the SBI MF content team
- An LLM API (e.g., OpenAI GPT-4, Google Gemini, or Groq) will be accessible for generation
- The project team has access to cloud vector database services (e.g., Pinecone, Weaviate, or pgvector)

---

## 8. Expected Outcomes

By the completion of this project, the following deliverables are expected:

1. **Functional AI Chatbot** deployed at a production-ready endpoint
2. **Knowledge Ingestion Pipeline** capable of processing new documents within 15 minutes
3. **Admin Dashboard** for document management, query analytics, and conversation logs
4. **Evaluation Report** demonstrating accuracy, latency, and user satisfaction benchmarks
5. **Technical Documentation** including architecture diagrams, API specs, and deployment runbooks
6. **Phase-wise Architecture Blueprint** detailing the system design across all development phases

---

## 9. Technology Stack (Proposed)

| Layer | Technology |
|---|---|
| **LLM** | OpenAI GPT-4o / Google Gemini 1.5 / Groq (LLaMA 3) |
| **Embedding Model** | `text-embedding-3-small` / `nomic-embed-text` |
| **Vector Store** | Pinecone / pgvector (PostgreSQL) / FAISS |
| **Orchestration** | LangChain / LlamaIndex |
| **Backend API** | FastAPI (Python) |
| **Frontend** | Next.js + TypeScript |
| **Database** | PostgreSQL (conversation history, metadata) |
| **Document Processing** | PyMuPDF, Unstructured.io, LangChain document loaders |
| **Containerization** | Docker + Docker Compose |
| **Cloud** | AWS / Azure (TBD) |
| **CI/CD** | GitHub Actions |
| **Monitoring** | LangSmith / Langfuse / Grafana |

---

*Document Version: 1.0 | Last Updated: May 2026 | Status: Approved for Development*
