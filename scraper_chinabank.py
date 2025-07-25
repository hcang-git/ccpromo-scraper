"""Contains functions to scrape promos (CC and others) from Chinabank website"""
import logging
import uuid
import time
import random
from datetime import date
from typing import List

from bs4 import BeautifulSoup

from utilities.core_utils import get_html_content
from utilities.classes import BankPromo


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def extract_cbank_href(html_str, unique_id):
    """
    Extracts the promo links in the href within the element gallery-list. 
    Logic especially for Chinabank website ao Jun 2025

    Args:
        html_str (str): Raw HTML.
        unique_id (str): UUID for trace logging.

    Returns:
        list of str: href content of matching elements.
    """
    try:
        soup = BeautifulSoup(html_str, "html.parser")
        # Find the outer div using its id (you can also use wire:id if needed)
        results = soup.find('div', id='gallery-list')
        # Extract all hrefs from <a> tags inside that div
        hrefs = [a['href'] for a in results.find_all('a', href=True)]
        return hrefs
    except Exception as e:
        logger.error("Request ID %s: Error extracting hrefs from link: %s", unique_id, e)
        return []

def extract_cbank_content(html_str, unique_id):
    """
    Extracts contents of the html_str to get promo details from Chinabank
    Logic especially for Chinabank website ao Jun 2025
    Args:
        html_str (str): Raw HTML.
        unique_id (str): UUID for trace logging.

    Returns:
        list of str: href content of matching elements.
    """
    try:
        soup = BeautifulSoup(html_str, "html.parser")
        # Find the outer div using its id (you can also use wire:id if needed)
        results = soup.find('div', id='article-detail')
        # Extract all hrefs from <a> tags inside that div
        text = results.get_text(separator='\n', strip=True)
        return text
    except Exception as e:
        logger.error("Request ID %s: Error extracting hrefs from link: %s", unique_id, e)
        return []

def scrape_chinabank() -> List[BankPromo]:
    """
    Scrapes credit card promo content from China Bank's promotional pages.

    Steps:
    1. Iterates through predefined category URLs.
    2. Extracts individual promo links (hrefs) from each category page.
    3. Fetches and parses content from each promo link.
    4. Structures each result into a BankPromo instance.
    5. Returns a list of all successfully scraped promos.

    Returns:
        List[BankPromo]: Standardized promo data from China Bank.
    """
    scrape_id = str(uuid.uuid4())
    logging.info(f"[ChinaBank] Starting scrape session: {scrape_id}")

    chinabank_promo_urls = [
        "https://www.chinabank.ph/credit-card-promos-more",
        "https://www.chinabank.ph/credit-card-promos-beauty-wellness",
        "https://www.chinabank.ph/credit-cards-promos-travel",
        "https://www.chinabank.ph/credit-cards-promos-stay",
        "https://www.chinabank.ph/credit-cards-promos-installment",
        "https://www.chinabank.ph/credit-cards-promos-ecom",
        "https://www.chinabank.ph/credit-cards-promos-shop",
        "https://www.chinabank.ph/credit-cards-promos-dine",
        "https://www.chinabank.ph/credit-cards-promos-premium",
        "https://www.chinabank.ph/credit-cards-promos-member-get-member",
    ]

    promos = []

    for idx_cat, category_url in enumerate(chinabank_promo_urls, start=1):
        logging.info(f"[ChinaBank] ({idx_cat}/{len(chinabank_promo_urls)}) Loading category: {category_url}")

        try:
            promo_url_content = get_html_content(category_url, unique_id=scrape_id)
            promo_hrefs = extract_cbank_href(promo_url_content, unique_id=scrape_id)
            logging.info(f"[ChinaBank] Found {len(promo_hrefs)} promo links in category")

            for idx_link, promo_url in enumerate(promo_hrefs, start=1):  # sample 2 per category
                logging.info(f"[ChinaBank] ({idx_link}) Fetching promo page: {promo_url}")

                try:
                    promo_html = get_html_content(promo_url, unique_id=scrape_id)
                    promo_txt = extract_cbank_content(promo_html, unique_id=scrape_id)

                    promo = BankPromo(
                        scrape_id = scrape_id,
                        bank_name="chinabank",
                        promo_url=promo_url,
                        promo_content=promo_txt,
                        scrape_date=date.today()
                    )

                    promos.append(promo)
                    logging.info(f"[ChinaBank] Promo scraped successfully from {promo_url}")

                except Exception as e:
                    logging.warning(f"[ChinaBank] Failed to extract promo content from {promo_url}: {e}")

                time.sleep(random.uniform(1, 5))

        except Exception as e:
            logging.warning(f"[ChinaBank] Failed to load category page {category_url}: {e}")

    logging.info(f"[ChinaBank] Completed scrape. {len(promos)} promos collected.")

    return promos
