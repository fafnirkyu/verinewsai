import ipaddress
import re
import socket
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


REDIRECT_STATUSES = {301, 302, 303, 307, 308}
MAX_REDIRECTS = 5


def is_url(text: str) -> bool:
    """Checks if the input string is a valid HTTP/HTTPS URL."""
    parsed = urlparse(text.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.hostname)


def _validate_public_url(url: str) -> None:
    """Rejects URLs that resolve to local, private, or reserved addresses."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only valid HTTP and HTTPS URLs are supported.")

    try:
        addresses = [ipaddress.ip_address(parsed.hostname)]
    except ValueError:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        try:
            address_info = socket.getaddrinfo(
                parsed.hostname,
                port,
                type=socket.SOCK_STREAM,
            )
        except socket.gaierror as exc:
            raise ValueError("The URL hostname could not be resolved.") from exc
        addresses = {
            ipaddress.ip_address(item[4][0])
            for item in address_info
        }

    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("The URL resolves to a non-public network address.")


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
        original_url = url.strip()
        current_url = original_url

        for _ in range(MAX_REDIRECTS + 1):
            _validate_public_url(current_url)
            response = requests.get(
                current_url,
                headers=headers,
                timeout=12,
                allow_redirects=False,
            )

            if response.status_code not in REDIRECT_STATUSES:
                response.raise_for_status()
                break

            location = response.headers.get("Location")
            if not location:
                raise ValueError("The URL returned a redirect without a destination.")
            current_url = urljoin(current_url, location)
        else:
            raise ValueError(f"The URL exceeded the {MAX_REDIRECTS}-redirect limit.")
        
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
            "url": current_url,
            "title": title.strip() if title else "Extracted Article",
            "content": body_text[:3500],  # Cap token size focused on main narrative
            "error": None
        }

    except Exception as e:
        return {
            "success": False,
            "url": url.strip(),
            "title": "Extraction Failed",
            "content": "",
            "error": str(e)
        }
