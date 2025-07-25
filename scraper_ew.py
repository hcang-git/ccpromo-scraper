"""Contains functions to scrape credit card promos from Eastwest Bank website"""
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

def get_ew_content(html_str, unique_id):
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
        main_tag = soup.find(
            class_="block block-system block-system-main-block block--ewb-theme-content block--system-main"
            )
        html_text = main_tag.get_text(separator='\n', strip=True)
        logger.info("Request ID %s: Extracted text", unique_id)
        return html_text
    except Exception as e:
        logger.error("Request ID %s: Error extracting text: %s", unique_id, e)
        return []

def scrape_ew() -> List[BankPromo]:
    """
    Scrapes promotional content from EastWest Bank's website.

    Steps:
    1. Generate a unique scrape session ID.
    2. Load and filter sitemap URLs for promotional pages.
    3. Extract and structure each promo as a BankPromo object.
    4. Return a list of all successfully scraped promos.

    Returns:
        List[BankPromo]: Standardized promo data from EastWest.
    """
    scrape_id = str(uuid.uuid4())
    logging.info(f"[EastWest] Starting scrape session: {scrape_id}")

    urls = get_sitemap_urls("https://www.eastwestbanker.com/sitemap.xml", unique_id=scrape_id)
    logging.info(f"[EastWest] Retrieved {len(urls)} URLs from sitemap")

    promo_urls = [url for url in urls if url.startswith("https://www.eastwestbanker.com/promos/")][:3]
    logging.info(f"[EastWest] Filtered {len(promo_urls)} promo URLs")

    promos = []

    for idx, url in enumerate(promo_urls, start=1):
        logging.info(f"[EastWest] ({idx}/{len(promo_urls)}) Fetching content from {url}")

        try:
            html_content = get_html_content(url, unique_id=scrape_id)
            html_txt = get_ew_content(html_content, unique_id=scrape_id)

            promo = BankPromo(
                scrape_id = scrape_id,
                bank_name="eastwest",
                promo_url=url,
                promo_content=html_txt,
                scrape_date=date.today()
            )

            promos.append(promo)
            logging.info(f"[EastWest] ({idx}/{len(promo_urls)}) Promo scraped successfully")

        except Exception as e:
            logging.warning(f"[EastWest] ({idx}/{len(promo_urls)}) Failed to scrape {url}: {e}")

        time.sleep(random.uniform(1, 5))  # polite scraping

    logging.info(f"[EastWest] Completed scrape. {len(promos)} promos collected.")

    return promos
