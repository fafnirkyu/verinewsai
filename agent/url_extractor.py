import re
import requests
from bs4 import BeautifulSoup

def is_url(text: str) -> bool:
    """Checks if the input string is a valid HTTP/HTTPS URL."""
    url_pattern = re.compile(
        r'^(https?://)'
        r'([a-zA-Z0-9.-]+(\.[a-zA-Z]{2,})+)'
        r'(:\d+)?'
        r'(/.*)?$'
    )
    return bool(url_pattern.match(text.strip()))

def extract_article_from_url(url: str) -> dict:
    """Fetches a URL and extracts only the primary article text, discarding sidebar noise."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/118.0.0.0 Safari/537.36"
        )
    }
    
    try:
        response = requests.get(url.strip(), headers=headers, timeout=12)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Strip out non-article metadata, sidebars, related links, and navigation
        for element in soup([
            "script", "style", "nav", "footer", "header", "aside", "form", 
            "iframe", "figcaption"
        ]):
            element.decompose()

        # Remove BBC/generic "Related Topics" or recommendation blocks
        for element in soup.find_all(class_=re.compile(r'(related|recommend|trending|sidebar|footer|promo|ad)', re.I)):
            element.decompose()
            
        # Extract title
        title = ""
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"]
        elif soup.title and soup.title.string:
            title = soup.title.string
        elif soup.h1:
            title = soup.h1.get_text()

        # Target primary content container first (<article> or <main>)
        content_area = soup.find("article") or soup.find("main") or soup
        
        paragraphs = content_area.find_all("p")
        text_lines = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 30]
        body_text = "\n\n".join(text_lines)

        if not body_text:
            body_text = content_area.get_text(separator="\n", strip=True)

        return {
            "success": True,
            "url": url,
            "title": title.strip() if title else "Extracted Article",
            "content": body_text[:3500],  # Cap token size focused on main narrative
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "url": url,
            "title": "Extraction Failed",
            "content": "",
            "error": str(e)
        }