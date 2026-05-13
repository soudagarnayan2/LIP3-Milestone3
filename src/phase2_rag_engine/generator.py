import logging
import os
from typing import List, Dict, Tuple
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)

class RAGGenerator:
    """
    Phase 2: LLM Generation & Strict Grounding.
    Handles self-query extraction and the final grounded response generation.
    """
    
    def __init__(self, use_mock: bool = False):
        self.use_mock = use_mock
        if not use_mock and "GROQ_API_KEY" in os.environ:
            # Using Llama 3.1 via Groq for blazing fast generation
            self.llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0)
        else:
            self.llm = None
            logger.warning("No GROQ_API_KEY found or mock mode enabled. Using dummy LLM responses.")

        self.extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an AI assistant for SBI Mutual Fund. Extract the exact 'fund_name' the user is asking about. Return ONLY a JSON object: {{\"fund_name\": \"...\"}}. If no specific fund is mentioned, return {{}}."),
            ("user", "{query}")
        ])

        self.qa_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the official SBI Mutual Fund virtual assistant.
Answer the user's question STRICTLY using the context provided below. 
Do NOT use outside knowledge. Do NOT hallucinate NAV values or risk profiles.
If the context does not contain the answer, say "I'm sorry, but I don't have that specific information in my official knowledge base."

Always cite the Source URL at the end of your response if you provide an answer.

CONTEXT:
{context}"""),
            ("user", "{query}")
        ])

    def extract_filters(self, query: str) -> Dict:
        """Uses LLM to extract metadata filters (Self-Querying)."""
        logger.info("Extracting metadata filters from query...")
        if self.use_mock or not self.llm:
            # Simple mock extraction for demonstration
            if "gold" in query.lower():
                return {"fund_name": "SBI Gold Fund"}
            elif "psu" in query.lower():
                return {"fund_name": "SBI PSU Fund"}
            return {}

        try:
            chain = self.extraction_prompt | self.llm
            response = chain.invoke({"query": query})
            import json
            filters = json.loads(response.content)
            logger.info(f"Extracted filters: {filters}")
            return filters
        except Exception as e:
            logger.error(f"Failed to extract filters: {e}")
            return {}

    def generate_answer(self, query: str, context_docs: List[Document], language: str = "en") -> Tuple[str, str]:
        """Generates a strictly grounded answer based on retrieved documents."""
        if not context_docs:
            return "I couldn't find any relevant fund information for your query.", ""

        # Format context
        context_str = "\n\n".join(
            f"Fund: {doc.metadata.get('fund_name')}\nURL: {doc.metadata.get('url')}\nDetails: {doc.page_content}"
            for doc in context_docs
        )
        
        # Extract citation URL (assuming k=1 for our Low Top-K strategy)
        citation_url = context_docs[0].metadata.get("url", "Unknown Source")

        logger.info("Generating grounded response...")
        if self.use_mock or not self.llm:
            # Mock response
            fund_name = context_docs[0].metadata.get('fund_name', 'the fund')
            answer = f"[MOCK] Based on the official documents, {fund_name} has a NAV of {context_docs[0].page_content.split('NAV:')[1].split('Investment')[0].strip()}."
            return answer, citation_url

        try:
            # Bilingual Pilot: Add Hindi instruction if requested
            prompt = self.qa_prompt
            if language == "hi":
                prompt = ChatPromptTemplate.from_messages([
                    ("system", self.qa_prompt.messages[0].prompt.template + "\n\nCRITICAL: You must translate and provide your final response entirely in Hindi (Devenagari script)."),
                    ("user", "{query}")
                ])

            chain = prompt | self.llm
            response = chain.invoke({"context": context_str, "query": query})
            return response.content, citation_url
        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            return "An error occurred while generating the response.", ""

if __name__ == "__main__":
    generator = RAGGenerator(use_mock=True)
    filters = generator.extract_filters("What is the NAV of the Gold fund?")
    print(filters)
