import os
import time
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VeriNewsSearch")

try:
    import serpapi
    HAS_SERPAPI = True
except ImportError:
    HAS_SERPAPI = False


class MultiEngineSearchTool:
    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.5):
        self.api_key = os.getenv("SERPAPI_API_KEY")
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY environment variable is not set in .env")

    def search(self, query: str, engine: str = "google_search") -> Dict[str, Any]:
        """Executes a search query with exponential backoff and empty-response safety guards."""
        clean_query = query.strip()
        
        # Map generic engine name to SerpApi expected string
        serpapi_engine = "google" if engine == "google_search" else engine

        params = {
            "q": clean_query,
            "engine": serpapi_engine,
            "api_key": self.api_key
        }

        results: Dict[str, Any] = {}
        attempt = 0

        # Retry loop for resilience against rate limits (429) or transient network drops
        while attempt < self.max_retries:
            try:
                if HAS_SERPAPI and hasattr(serpapi, "Client"):
                    client = serpapi.Client(api_key=self.api_key)
                    res_obj = client.search(params)
                    results = res_obj.as_dict() if hasattr(res_obj, "as_dict") else dict(res_obj)
                elif HAS_SERPAPI and hasattr(serpapi, "search"):
                    results = serpapi.search(params)
                else:
                    raise ImportError("SerpApi client library missing. Install via `pip install serpapi`.")
                
                # Success break
                break

            except Exception as e:
                attempt += 1
                logger.warning(
                    f"[SerpApi Retry {attempt}/{self.max_retries}] Engine: '{engine}' | Query: '{clean_query}' | Error: {e}"
                )
                if attempt >= self.max_retries:
                    logger.error(f"[SerpApi Failed] Max retries exhausted for engine '{engine}'. Returning fallback dict.")
                    return {
                        "engine": engine,
                        "sub_query": clean_query,
                        "results": [],
                        "status": "failed",
                        "error": str(e)
                    }
                time.sleep(self.backoff_factor ** attempt)

        parsed_snippets: List[Dict[str, Any]] = []

        # Parse engine-specific payloads safely
        if engine == "google_news" and "news_results" in results:
            for item in results.get("news_results", [])[:5]:
                source_val = item.get("source")
                source_name = source_val.get("name") if isinstance(source_val, dict) else (source_val or "Google News")
                snippet_text = item.get("snippet") or item.get("highlight", {}).get("snippet", "") or item.get("title", "")
                
                parsed_snippets.append({
                    "title": item.get("title", "No Title"),
                    "link": item.get("link", ""),
                    "snippet": snippet_text,
                    "source_name": source_name,
                    "date": item.get("date", "N/A")
                })

        elif engine == "google_scholar" and "organic_results" in results:
            for item in results.get("organic_results", [])[:5]:
                pub_info = item.get("publication_info", {}).get("summary", "")
                parsed_snippets.append({
                    "title": item.get("title", "No Title"),
                    "link": item.get("link", "") or item.get("result_id", ""),
                    "snippet": item.get("snippet", "") or item.get("title", ""),
                    "source_name": "Google Scholar",
                    "date": pub_info
                })

        elif engine == "google_patents" and "organic_results" in results:
            for item in results.get("organic_results", [])[:5]:
                parsed_snippets.append({
                    "title": item.get("title", "No Title"),
                    "link": item.get("pdf", "") or item.get("patent_id", ""),
                    "snippet": item.get("snippet", "") or item.get("title", ""),
                    "source_name": "Google Patents",
                    "date": item.get("publication_date", "N/A")
                })

        else:  # Fallback to standard Google Organic search
            for item in results.get("organic_results", [])[:5]:
                snippet_text = item.get("snippet") or item.get("snippet_highlighted_words", "") or item.get("title", "")
                parsed_snippets.append({
                    "title": item.get("title", "No Title"),
                    "link": item.get("link", ""),
                    "snippet": snippet_text,
                    "source_name": item.get("displayed_link", "Google Search"),
                    "date": item.get("date", "N/A")
                })

        # Report empty SERP status cleanly
        status = "success" if parsed_snippets else "empty_serp"

        return {
            "engine": engine,
            "sub_query": clean_query,
            "results": parsed_snippets,
            "status": status
        }