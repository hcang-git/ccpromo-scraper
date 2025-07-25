"""Contains utility functions used by the other scrapers"""
import logging
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def get_sitemap_urls(sitemap_url, unique_id):
    """
    Fetches and parses a sitemap XML, returning all <loc> URLs,
    and logs using the provided unique_id.

    Args:
        sitemap_url (str): URL to the sitemap.xml
        unique_id (str): A unique ID for traceable logging

    Returns:
        List[str]: Extracted URLs from the sitemap
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )
    }

    try:
        logger.info("Request ID %s: Requesting sitemap from %s", unique_id, sitemap_url)
        response = requests.get(sitemap_url, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info("Request ID %s: Received sitemap with status code %d", unique_id, response.status_code)
    except requests.RequestException as e:
        logger.error("Request ID %s: HTTP request failed: %s", unique_id, e)
        raise RuntimeError(f"Request failed: {e}") from e

    try:
        root = ET.fromstring(response.content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [elem.text for elem in root.findall('.//ns:loc', namespace)]
        logger.info("Request ID %s: Extracted %d URLs from sitemap", unique_id, len(urls))
        return urls
    except ET.ParseError as e:
        logger.error("Request ID %s: Failed to parse XML: %s", unique_id, e)
        raise ValueError(f"XML parsing failed: {e}") from e

def get_html_content(url, unique_id):
    """
    Fetches the raw HTML content of a given URL and logs events using the provided unique_id.

    Args:
        url (str): The target webpage URL to fetch.
        unique_id (str): A unique identifier used for logging and traceability.

    Returns:
        str | None: The raw HTML content of the page if successful, or None if the request fails.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )
    }

    try:
        logger.info("Request ID %s: Fetching HTML content from %s", unique_id, url)
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info("Request ID %s: Received HTML with status code %d", unique_id, response.status_code)
        return response.text
    except requests.RequestException as e:
        logger.error("Request ID %s: Failed to fetch HTML: %s", unique_id, e)
        return None
    

def html_to_text(html: str) -> str:
    """Converts HTML to plain text safely."""
    return BeautifulSoup(html or "", "html.parser").get_text(separator="\n", strip=True)
