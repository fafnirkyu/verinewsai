import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()
logger = logging.getLogger("VeriNewsContext")


class HybridContextEngine:
    def __init__(self, token_threshold: int = 12000):
        self.token_threshold = token_threshold
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Gemini API key not found in environment variables.")

        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=api_key
        )

    def prepare_evidence(
        self, 
        research_data: List[Dict[str, Any]], 
        deep_scrape_docs: List[Document] = None
    ) -> Dict[str, Any]:
        """Normalizes search evidence into structured context with robust zero-hit handling."""
        all_documents: List[Document] = []

        for task in research_data:
            engine = task.get("engine", "unknown")
            results = task.get("results", [])

            if not isinstance(results, list):
                continue

            for item in results:
                title = item.get("title", "No Title")
                snippet = item.get("snippet", "") or item.get("abstract", "") or title
                link = item.get("link", "") or item.get("pdf_link", "") or item.get("patent_id", "")
                pub_date = item.get("date", "") or item.get("publication_date", "N/A")
                source_name = item.get("source_name") or item.get("source", engine)

                content = (
                    f"[{source_name.upper()} | Date: {pub_date}]\n"
                    f"Title: {title}\n"
                    f"URL: {link}\n"
                    f"Snippet/Details: {snippet}"
                )

                all_documents.append(Document(
                    page_content=content, 
                    metadata={"source": source_name, "link": link, "engine": engine}
                ))

        if deep_scrape_docs:
            all_documents.extend(deep_scrape_docs)

        # Edge Case Safeguard: No search evidence recovered
        if not all_documents:
            logger.warning("Zero search documents recovered across all engines.")
            return {
                "mode": "empty_fallback",
                "context_text": "NO LIVE SEARCH EVIDENCE RETRIEVED. ALL SEARCH ENGINES RETURNED EMPTY OR FAILED.",
                "total_sources": 0,
                "word_count": 0
            }

        total_word_count = sum(len(doc.page_content.split()) for doc in all_documents)

        if total_word_count < self.token_threshold and not deep_scrape_docs:
            formatted_context = "\n\n---\n\n".join([doc.page_content for doc in all_documents])
            return {
                "mode": "direct_context",
                "context_text": formatted_context,
                "total_sources": len(all_documents),
                "word_count": total_word_count
            }
        else:
            vector_store = FAISS.from_documents(all_documents, self.embeddings)
            return {
                "mode": "faiss_rag",
                "vector_store": vector_store,
                "total_sources": len(all_documents),
                "word_count": total_word_count
            }

    def get_context_text(self, vector_store: FAISS, query: str, k: int = 6) -> str:
        docs = vector_store.similarity_search(query, k=k)
        return "\n\n---\n\n".join([doc.page_content for doc in docs])