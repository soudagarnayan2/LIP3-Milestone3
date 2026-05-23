import os
import re
import sys
import time
import json
import logging
from typing import List, Dict, Tuple
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Add workspace root to python path to ensure relative imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

# Load environment variables early
load_dotenv()

# Set logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Streamlit Page Config
st.set_page_config(
    page_title="SBI Mutual Fund FAQ - RAG Playground",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling (Dark Mode Accent)
st.markdown("""
<style>
    /* Main Background & Text */
    .main {
        background-color: #0b0f19;
        color: #f3f4f6;
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: #00d09c !important;
        font-family: 'Outfit', 'Inter', sans-serif;
    }
    
    /* Card/Metric Styling */
    .metric-card {
        background-color: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .metric-val {
        font-size: 2rem;
        font-weight: bold;
        color: #00d09c;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Chat bubble styles */
    .user-bubble {
        background-color: #1f2937;
        color: #f3f4f6;
        padding: 12px 18px;
        border-radius: 18px 18px 0px 18px;
        margin: 10px 0;
        text-align: right;
        display: inline-block;
        float: right;
        clear: both;
        max-width: 80%;
    }
    
    .bot-bubble {
        background-color: #111827;
        color: #f3f4f6;
        border: 1px solid #00d09c33;
        padding: 12px 18px;
        border-radius: 18px 18px 18px 0px;
        margin: 10px 0;
        text-align: left;
        display: inline-block;
        float: left;
        clear: both;
        max-width: 80%;
    }
    
    .citation-link {
        color: #00d09c;
        text-decoration: none;
        font-weight: 500;
        font-size: 0.85rem;
    }
    
    .citation-link:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

# Helper function for PII Guardrails
def detect_pii(text: str) -> Dict[str, List[str]]:
    """Looks for PII in the query and returns match groupings."""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    phone_pattern = r'\b\d{10}\b'
    aadhaar_pattern = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
    pan_pattern = r'\b[A-Z]{5}\d{4}[A-Z]{1}\b'
    
    found = {}
    emails = re.findall(email_pattern, text)
    if emails: found["Email"] = emails
    
    phones = re.findall(phone_pattern, text)
    if phones: found["Phone"] = phones
    
    aadhaars = re.findall(aadhaar_pattern, text)
    if aadhaars: found["Aadhaar"] = aadhaars
    
    pans = re.findall(pan_pattern, text)
    if pans: found["PAN Card"] = pans
    
    return found

# Lazy load RAG modules so streamlit app starts immediately even if models load slowly
@st.cache_resource
def get_hybrid_retriever():
    try:
        from src.phase2_rag_engine.retriever import HybridRetriever
        return HybridRetriever()
    except Exception as e:
        st.error(f"Error loading HybridRetriever: {e}")
        return None

# Load available raw data for statistics
@st.cache_data
def load_kb_stats() -> Tuple[int, List[Dict]]:
    try:
        raw_data_path = "src/phase1_ingestion/data/embedded_chunks.json"
        if os.path.exists(raw_data_path):
            with open(raw_data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return len(data), data
        return 0, []
    except Exception:
        return 0, []

# Initialize Session States
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = os.getenv("GROQ_API_KEY", "")

# --- SIDEBAR: Parameter Tuning & Controls ---
st.sidebar.title("🛠️ Playground Configurations")
st.sidebar.markdown("Fine-tune the RAG parameters in real-time.")

# API Settings
st.sidebar.subheader("🔑 API Authentication")
api_key_input = st.sidebar.text_input(
    "Groq API Key", 
    value=st.session_state.groq_api_key, 
    type="password",
    help="Needed to run generator and self-query extraction if not set in your .env file."
)
if api_key_input:
    st.session_state.groq_api_key = api_key_input
    os.environ["GROQ_API_KEY"] = api_key_input

# LLM Model Settings
st.sidebar.subheader("🤖 LLM Parameters")
selected_model = st.sidebar.selectbox(
    "LLM Model",
    ["llama-3.1-8b-instant", "llama3-8b-8192", "mixtral-8x7b-32768"],
    index=0,
    help="Select the generation model hosted on Groq."
)
temperature = st.sidebar.slider(
    "Temperature", 
    min_value=0.0, 
    max_value=1.0, 
    value=0.0, 
    step=0.1,
    help="Higher values make responses more creative but less predictable."
)

# RAG Settings
st.sidebar.subheader("🔍 Retrieval Settings")
retrieval_strategy = st.sidebar.selectbox(
    "Retrieval Strategy",
    ["Hybrid (FAISS + BM25)", "Semantic Only (FAISS)", "Keyword Only (BM25)"],
    index=0,
    help="Hybrid combines vector search with keyword matching."
)
top_k = st.sidebar.slider(
    "Top-K Chunks", 
    min_value=1, 
    max_value=5, 
    value=1,
    help="Number of document chunks passed to the LLM context. Phase 3 recommends Top-K=1 for precision."
)

# Guardrails
st.sidebar.subheader("🛡️ Safety & Guardrails")
pii_redaction = st.sidebar.checkbox("Enable PII Guardrails", value=True, help="Reject queries containing emails, phone numbers, Aadhaar or PAN cards.")
hindi_mode = st.sidebar.checkbox("Force Bilingual Translation (Hindi)", value=False, help="Instruct the LLM to write answers in Devanagari Hindi script.")

# About Project
st.sidebar.divider()
st.sidebar.markdown("### Project Metadata")
st.sidebar.info(
    "**SBI Mutual Fund FAQ Bot**  \n"
    "Phase 7 Streamlit Playground  \n"
    "Embeddings: BAAI/bge-small-en-v1.5 (384d)  \n"
    "Vector Store: FAISS"
)

# Main Title & KPI Cards
st.title("🚀 SBI Mutual Fund AI Chatbot")
st.write("Welcome to the **Phase 7 Interactive Playground & Prototyping Sandbox**.")

# Fetch statistics
total_chunks, raw_chunks = load_kb_stats()
unique_funds = len(set(c["metadata"].get("fund_name", "") for c in raw_chunks if "metadata" in c))

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{unique_funds}</div><div class="metric-label">Indexed Funds</div></div>', unsafe_allow_html=True)
with kpi2:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{total_chunks}</div><div class="metric-label">Total Document Chunks</div></div>', unsafe_allow_html=True)
with kpi3:
    st.markdown(f'<div class="metric-card"><div class="metric-val">384</div><div class="metric-label">Embedding Dimensions</div></div>', unsafe_allow_html=True)
with kpi4:
    st.markdown(f'<div class="metric-card"><div class="metric-val">Uvicorn Port 8000</div><div class="metric-label">API Backend Port</div></div>', unsafe_allow_html=True)

st.write("")

# Create Tabs
tab_chat, tab_inspector, tab_comparison, tab_kb = st.tabs([
    "💬 Interactive Chat Sandbox", 
    "🧪 Step-by-Step Query Inspector", 
    "⚖️ Grounded vs Vanilla LLM Comparison", 
    "📊 Knowledge Base Explorer"
])

# Load Retriever Resource
retriever = get_hybrid_retriever()

# Initialize LLM for local use in streamlit playground
def run_generator(query: str, docs: List[Document], temp: float, model: str, lang: str) -> Tuple[str, str, float]:
    """Generates an answer using the playground configured LLM settings."""
    if not st.session_state.groq_api_key:
        return "⚠️ Error: Please input your Groq API Key in the sidebar configuration to test the generator.", "", 0.0
    
    start_time = time.time()
    try:
        llm = ChatGroq(model_name=model, temperature=temp, groq_api_key=st.session_state.groq_api_key)
        
        # Build prompt
        qa_system_template = """You are the official SBI Mutual Fund virtual assistant.
Answer the user's question STRICTLY using the context provided below. 
Do NOT use outside knowledge. Do NOT hallucinate NAV values or risk profiles.
If the context does not contain the answer, say "I'm sorry, but I don't have that specific information in my official knowledge base."

Always cite the Source URL at the end of your response if you provide an answer.

CONTEXT:
{context}"""
        
        if lang == "hi":
            qa_system_template += "\n\nCRITICAL: You must translate and provide your final response entirely in Hindi (Devanagari script)."
            
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", qa_system_template),
            ("user", "{query}")
        ])
        
        # Format context
        context_str = "\n\n".join(
            f"Fund: {doc.metadata.get('fund_name')}\nURL: {doc.metadata.get('url')}\nDetails: {doc.page_content}"
            for doc in docs
        )
        citation_url = docs[0].metadata.get("url", None) if docs else None
        
        chain = qa_prompt | llm
        response = chain.invoke({"context": context_str, "query": query})
        latency = time.time() - start_time
        
        # Null-citation check: If LLM fallback occurs, omit source URL
        fallback_phrases = ["i couldn't find", "i don't have that specific information", "i'm sorry"]
        answer = response.content
        if any(phrase in answer.lower() for phrase in fallback_phrases):
            citation_url = None
            
        return answer, citation_url, latency
    except Exception as e:
        return f"Error executing generation: {e}", "", time.time() - start_time

def run_self_query(query: str) -> Dict:
    """Extracts metadata filters using LLM."""
    if not st.session_state.groq_api_key:
        # Fallback to simple matching if API key missing
        if "gold" in query.lower(): return {"fund_name": "SBI Gold Fund"}
        if "psu" in query.lower(): return {"fund_name": "SBI PSU Fund"}
        if "contra" in query.lower(): return {"fund_name": "SBI Contra Fund"}
        return {}
        
    try:
        llm = ChatGroq(model_name=selected_model, temperature=0, groq_api_key=st.session_state.groq_api_key)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an AI assistant for SBI Mutual Fund. Extract the exact 'fund_name' the user is asking about. Return ONLY a JSON object: {{\"fund_name\": \"...\"}}. If no specific fund is mentioned, return {{}}."),
            ("user", "{query}")
        ])
        chain = prompt | llm
        response = chain.invoke({"query": query})
        return json.loads(response.content)
    except Exception:
        # Quiet fallback
        return {}

# Perform retrieval with strategy overrides
def perform_retrieval(query: str, filters: Dict, strategy: str, k: int) -> List[Document]:
    if not retriever:
        return []
        
    # Dynamically apply Top-K configuration to internal retrievers
    if retriever.semantic_retriever:
        retriever.semantic_retriever.search_kwargs["k"] = k
    if retriever.keyword_retriever:
        retriever.keyword_retriever.k = k
        
    # Retrieve
    if strategy == "Semantic Only (FAISS)":
        if filters and retriever.faiss_vectorstore:
            ret = retriever.faiss_vectorstore.as_retriever(search_kwargs={"k": k, "filter": filters})
        else:
            ret = retriever.semantic_retriever
        return ret.invoke(query) if ret else []
        
    elif strategy == "Keyword Only (BM25)":
        docs = retriever.keyword_retriever.invoke(query) if retriever.keyword_retriever else []
        # Manual keyword post-filtering if filters present
        if filters:
            docs = [d for d in docs if all(d.metadata.get(key) == val for key, val in filters.items())]
        return docs[:k]
        
    else: # Hybrid (Ensemble)
        return retriever.retrieve(query, metadata_filters=filters)

# ----------------- TAB 1: INTERACTIVE CHAT -----------------
with tab_chat:
    st.subheader("💬 Chat Sandbox")
    st.write("Submit queries to test the end-to-end RAG response generation and safety guardrails.")
    
    # Prompt presets for quick testing
    col_pre1, col_pre2, col_pre3, col_pre4 = st.columns(4)
    with col_pre1:
        if st.button("What is the NAV of SBI Gold Fund?", use_container_width=True):
            user_input = "What is the NAV of SBI Gold Fund?"
            st.session_state.chat_history.append({"role": "user", "text": user_input})
    with col_pre2:
        if st.button("Is the SBI Contra Fund high risk?", use_container_width=True):
            user_input = "Is the SBI Contra Fund high risk?"
            st.session_state.chat_history.append({"role": "user", "text": user_input})
    with col_pre3:
        if st.button("How is the weather in Delhi?", use_container_width=True):
            user_input = "How is the weather in Delhi?"
            st.session_state.chat_history.append({"role": "user", "text": user_input})
    with col_pre4:
        if st.button("My phone is 9988776655, check Gold Fund NAV", use_container_width=True):
            user_input = "My phone is 9988776655, check Gold Fund NAV"
            st.session_state.chat_history.append({"role": "user", "text": user_input})

    # Main Chat Area Container
    chat_container = st.container()
    
    # Chat Input
    query_box = st.chat_input("Ask something about SBI Mutual Funds...")
    
    if query_box:
        st.session_state.chat_history.append({"role": "user", "text": query_box})
        
    # Render chat history
    with chat_container:
        for idx, msg in enumerate(st.session_state.chat_history):
            if msg["role"] == "user":
                st.markdown(f'<div class="user-bubble"><b>You:</b><br>{msg["text"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="bot-bubble"><b>Groww Assistant:</b><br>{msg["text"]}</div>', unsafe_allow_html=True)
                if "citation" in msg and msg["citation"]:
                    st.markdown(f'<div style="float: left; clear: both; margin-top:-5px; padding-left:18px;"><a class="citation-link" href="{msg["citation"]}" target="_blank">🔗 Source Document Citation</a></div>', unsafe_allow_html=True)
                
                # Show metadata expander below the bot answer for debugging
                if "meta" in msg:
                    with st.expander(f"🔍 RAG Pipeline Metadata (Turn {idx})", expanded=False):
                        st.json(msg["meta"])
                        
        # Handle new user message
        if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
            latest_query = st.session_state.chat_history[-1]["text"]
            
            with st.spinner("Processing through RAG Pipeline..."):
                # 1. PII check
                pii_matches = detect_pii(latest_query)
                if pii_redaction and pii_matches:
                    err_msg = "⚠️ Request rejected: Personal Identifiable Information (PII) detected."
                    meta = {"pii_detected": True, "pii_details": pii_matches}
                    st.session_state.chat_history.append({"role": "bot", "text": err_msg, "meta": meta})
                    st.rerun()
                
                # 2. Self-Querying Filter Extraction
                filters = run_self_query(latest_query)
                
                # 3. Retrieve Context
                start_retrieval = time.time()
                docs = perform_retrieval(latest_query, filters, retrieval_strategy, top_k)
                retrieval_latency = time.time() - start_retrieval
                
                # 4. Generate Answer
                lang_code = "hi" if hindi_mode else "en"
                answer, citation, gen_latency = run_generator(latest_query, docs, temperature, selected_model, lang_code)
                
                # Compile metadata log
                meta_log = {
                    "self_query_filters": filters,
                    "retrieval_strategy": retrieval_strategy,
                    "retrieved_docs_count": len(docs),
                    "retrieval_latency_sec": round(retrieval_latency, 3),
                    "generation_latency_sec": round(gen_latency, 3),
                    "total_latency_sec": round(retrieval_latency + gen_latency, 3),
                    "citations_url": citation,
                    "retrieved_contents": [
                        {
                            "content": d.page_content,
                            "metadata": d.metadata
                        } for d in docs
                    ]
                }
                
                st.session_state.chat_history.append({
                    "role": "bot",
                    "text": answer,
                    "citation": citation,
                    "meta": meta_log
                })
                st.rerun()

    # Clear chat option
    if st.session_state.chat_history:
        st.write("")
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()


# ----------------- TAB 2: STEP-BY-STEP INSPECTOR -----------------
with tab_inspector:
    st.subheader("🧪 Step-by-Step Query Inspector")
    st.write("Inspect how data flows through and gets modified by each phase of the RAG pipeline.")
    
    inspect_query = st.text_input("Enter Query to Inspect:", "What is the NAV of SBI PSU Fund?")
    
    if st.button("🔍 Inspect Pipeline Flow", type="primary"):
        # Phase 0: Guardrails Check
        st.markdown("### Phase 0: Input Guardrails & PII Analysis")
        pii_found = detect_pii(inspect_query)
        if pii_found:
            st.error("❌ PII Detected!")
            st.json(pii_found)
        else:
            st.success("✅ Clean Query (No PII Detected)")
            
        # Phase 1: Self Query Filter Extraction
        st.markdown("### Phase 1: Self-Querying & Metadata Extraction")
        filters = run_self_query(inspect_query)
        st.write("Extracted Filters for Vector Search Database:")
        st.json(filters)
        
        # Phase 2: Retrieval Matching
        st.markdown("### Phase 2: In-Depth Retrieval Match Details")
        
        # Pull semantic vs keyword separately to compare scores/matches
        col_sem, col_key = st.columns(2)
        
        with col_sem:
            st.markdown("**FAISS (Semantic Chunks)**")
            if retriever and retriever.faiss_vectorstore:
                # Query FAISS directly to display similarity scores
                semantic_results = retriever.faiss_vectorstore.similarity_search_with_score(
                    inspect_query, 
                    k=top_k, 
                    filter=filters if filters else None
                )
                if semantic_results:
                    for doc, score in semantic_results:
                        st.info(
                            f"**Content:** {doc.page_content}  \n"
                            f"**Fund:** {doc.metadata.get('fund_name')} | **L2 Distance Score:** {round(float(score), 4)}  \n"
                            f"**URL:** {doc.metadata.get('url')}"
                        )
                else:
                    st.write("No semantic matches found.")
            else:
                st.write("Semantic retriever index not loaded.")
                
        with col_key:
            st.markdown("**BM25 (Keyword Chunks)**")
            if retriever and retriever.keyword_retriever:
                keyword_results = retriever.keyword_retriever.invoke(inspect_query)
                if filters:
                    keyword_results = [d for d in keyword_results if all(d.metadata.get(key) == val for key, val in filters.items())]
                keyword_results = keyword_results[:top_k]
                
                if keyword_results:
                    for doc in keyword_results:
                        st.info(
                            f"**Content:** {doc.page_content}  \n"
                            f"**Fund:** {doc.metadata.get('fund_name')}  \n"
                            f"**URL:** {doc.metadata.get('url')}"
                        )
                else:
                    st.write("No keyword matches found.")
            else:
                st.write("Keyword retriever index not loaded.")
                
        # Phase 3: Generation Grounding Prompt Construction
        st.markdown("### Phase 3: LLM Context Assembly")
        docs = perform_retrieval(inspect_query, filters, retrieval_strategy, top_k)
        context_str = "\n\n".join(
            f"Fund: {doc.metadata.get('fund_name')}\nURL: {doc.metadata.get('url')}\nDetails: {doc.page_content}"
            for doc in docs
        )
        
        st.text_area("System Context Sent to LLM Prompt Template:", value=context_str, height=150, disabled=True)
        
        # Generation response
        st.markdown("### Phase 4: Generated Output Response")
        lang_code = "hi" if hindi_mode else "en"
        answer, citation, latency = run_generator(inspect_query, docs, temperature, selected_model, lang_code)
        st.write(f"**Answer Output ({round(latency, 2)}s):**")
        st.write(answer)
        if citation:
            st.markdown(f"**Source Citation URL:** [{citation}]({citation})")


# ----------------- TAB 3: COMPARISON SANDBOX -----------------
with tab_comparison:
    st.subheader("⚖️ Grounded vs Vanilla LLM Comparison")
    st.write("Demonstrate the power of RAG by comparing responses from a Vanilla LLM vs a Context-Grounded LLM.")
    
    comp_query = st.text_input("Compare Query:", "What is the NAV of SBI PSU Fund?", key="comp_query_input")
    
    if st.button("⚖️ Compare Side-by-Side"):
        if not st.session_state.groq_api_key:
            st.error("Please input your Groq API Key in the sidebar configuration to run this comparison.")
        else:
            col_rag, col_vanilla = st.columns(2)
            
            with col_rag:
                st.markdown("#### 🌟 Grounded RAG Response")
                with st.spinner("Retrieving and generating..."):
                    filters = run_self_query(comp_query)
                    docs = perform_retrieval(comp_query, filters, retrieval_strategy, top_k)
                    rag_answer, citation, rag_lat = run_generator(comp_query, docs, temperature, selected_model, "en")
                    
                    st.success(f"Response generated in {round(rag_lat, 2)}s")
                    st.write(rag_answer)
                    if citation:
                        st.markdown(f"**Source:** [{citation}]({citation})")
                    
                    with st.expander("Retrieved Context Chunks Used"):
                        for idx, d in enumerate(docs):
                            st.caption(f"Chunk {idx+1} ({d.metadata.get('fund_name')})")
                            st.write(d.page_content)
                            
            with col_vanilla:
                st.markdown("#### 🔴 Vanilla LLM (Direct API Call)")
                with st.spinner("Calling LLM directly without RAG context..."):
                    start_vanilla = time.time()
                    try:
                        llm_direct = ChatGroq(model_name=selected_model, temperature=temperature, groq_api_key=st.session_state.groq_api_key)
                        prompt = ChatPromptTemplate.from_messages([
                            ("system", "You are a general knowledge chatbot assistant. Answer the query directly based on your training parameters."),
                            ("user", "{query}")
                        ])
                        chain = prompt | llm_direct
                        vanilla_response = chain.invoke({"query": comp_query})
                        vanilla_lat = time.time() - start_vanilla
                        
                        st.warning(f"Response generated in {round(vanilla_lat, 2)}s")
                        st.write(vanilla_response.content)
                        st.caption("⚠️ Notice: Note how the vanilla LLM might struggle with exact and current NAV values, expense ratios, or state that it doesn't have live index data.")
                    except Exception as e:
                        st.error(f"Error calling direct LLM: {e}")


# ----------------- TAB 4: KNOWLEDGE BASE EXPLORER -----------------
with tab_kb:
    st.subheader("📊 Knowledge Base Explorer & Analytics")
    st.write("Browse through the documents and chunks stored locally inside the FAISS vector index database.")
    
    if raw_chunks:
        # Convert to Pandas Dataframe for display
        rows = []
        for idx, c in enumerate(raw_chunks):
            meta = c.get("metadata", {})
            rows.append({
                "Index ID": idx,
                "Fund Name": meta.get("fund_name", "Unknown"),
                "Source URL": meta.get("url", "Unknown"),
                "Content Details": c.get("page_content", "")[:120] + "...",
                "Tokens (Approx)": len(c.get("page_content", "").split())
            })
        df = pd.DataFrame(rows)
        
        # Filtering by Fund
        funds_list = ["All"] + list(df["Fund Name"].unique())
        selected_fund_filter = st.selectbox("Filter explorer by Fund Name:", funds_list)
        
        filtered_df = df
        if selected_fund_filter != "All":
            filtered_df = df[df["Fund Name"] == selected_fund_filter]
            
        st.dataframe(filtered_df, use_container_width=True)
        
        # Knowledge Base Operations
        st.markdown("### ⚙️ Database Controls")
        col_op1, col_op2 = st.columns(2)
        with col_op1:
            if st.button("🔄 Refresh Local Statistics"):
                st.cache_data.clear()
                st.rerun()
        with col_op2:
            st.write("Deploying scheduler pipelines and automated data refreshes can be inspected via Phase 1 chron scripts.")
    else:
        st.warning("No local index chunks found. Please check if Phase 1 ingestion is run and data files are generated in `src/phase1_ingestion/data/`.")
