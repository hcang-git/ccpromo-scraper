"""Contains functions to scrape promos (CC and others) from BPI website"""
import logging
import uuid
import time
import random
from datetime import date
from typing import List

from bs4 import BeautifulSoup

from utilities.core_utils import get_sitemap_urls, get_html_content
from utilities.classes import BankPromo

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def get_bpi_content(html_str, unique_id):
    """
    Extracts the text content of the element matching the given CSS selector.

    Args:
        html_str (str): Raw HTML.
        unique_id (str): UUID for trace logging.

    Returns:
        str: Text content of html_str.
    """
    try:
        soup = BeautifulSoup(html_str, "html.parser")
        main_tag = soup.find('main',
                             class_="container responsivegrid aem-GridColumn aem-GridColumn--default--12"
                             )
        html_text = main_tag.get_text(separator='\n', strip=True)
        logger.info("Request ID %s: Extracted texted", unique_id)
        return html_text
    except Exception as e:
        logger.error("Request ID %s: Error extracting text: %s", unique_id, e)
        return []

def scrape_bpi() -> List[BankPromo]:
    """
    Scrapes promotional content from BPI's website.

    This function performs the following steps:
    1. Generates a unique scrape session ID.
    2. Retrieves URLs from BPI's sitemap.
    3. Filters promo-related URLs from the sitemap.
    4. For each promo URL:
       - Fetches the HTML content.
       - Extracts the main promo content using a custom parser.
       - Builds a BankPromo object with metadata.
    5. Returns a list of BankPromo instances with standardized structure.

    Returns:
        List[BankPromo]: A list of promo data scraped from BPI, each containing:
            - bank_name (str)
            - promo_url (HttpUrl)
            - promo_content (str)
            - scrape_date (date): The current date of scraping.
    """

    scrape_id = str(uuid.uuid4())  # Unique ID for logging/tracing the scrape session
    logging.info(f"[BPI] Starting scrape session: {scrape_id}")

    # Retrieve all sitemap URLs from BPI's sitemap
    urls = get_sitemap_urls("https://www.bpi.com.ph/sitemap.xml", unique_id=scrape_id)

    # Filter URLs that are actual promotional pages (limit to first 2 for testing/speed)
    promo_urls = [
        url for url in urls 
        if url.startswith("https://www.bpi.com.ph/personal/rewards-and-promotions/")
    ]
    logging.info(f"[BPI] Filtered {len(promo_urls)} promo URLs")

    promos = []

    for idx, url in enumerate(promo_urls, start=1):
        try:
            html_content = get_html_content(url, unique_id=scrape_id)
            html_txt = get_bpi_content(html_content, unique_id=scrape_id)

            promo = BankPromo(
                scrape_id = scrape_id,
                bank_name="bpi",
                promo_url=url,
                promo_content=html_txt,
                scrape_date=date.today()
            )

            promos.append(promo)
            logging.info(f"[BPI] ({idx}/{len(promo_urls)}) Promo scraped successfully")

        except Exception as e:
            logging.warning(f"[BPI] ({idx}/{len(promo_urls)}) Failed to scrape {url}: {e}")

        promos.append(promo)

        # Sleep randomly to mimic human behavior and avoid blocking
        time.sleep(random.uniform(1, 5))

    logging.info(f"[BPI] Completed scrape. {len(promos)} promos collected.")
    return promos
