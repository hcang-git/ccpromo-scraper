"""Contains functions to scrape BDO credit card promos."""
import json
import logging
import uuid
import time
import random
import requests
from datetime import date
from typing import List

from utilities.classes import BankPromo
from utilities.core_utils import html_to_text

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def fetch_json_post(url, headers, payload, unique_id, timeout=5):
    """
    Sends a POST request to the specified URL with the provided headers and payload,
    and returns the response parsed as JSON.

    Args:
        url (str): The API endpoint to send the POST request to.
        headers (dict): HTTP headers to include in the request (e.g., Authorization, Content-Type).
        payload (dict): The JSON payload to send in the request body.
        unique_id (str): A unique identifier for this request, used in logging for traceability.
        timeout (int): Maximum time to wait for a response, in seconds. Defaults to 5.

    Returns:
        dict: The JSON-parsed response from the server.

    Raises:
        RuntimeError: If the request encounters an HTTP error or other connection issue.
        ValueError: If the response body is not valid JSON.
    """
    # Attempt to send the POST request
    try:
        logger.info("Request ID %s: Requesting response from %s", unique_id, url)
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        # Raise an HTTPError for bad responses (4xx or 5xx)
        response.raise_for_status()
        logger.info("Request ID %s: Received response with status code %d", 
                    unique_id, response.status_code
                    )

    except requests.exceptions.RequestException as e:
        # Log and raise a runtime error if any request-level exception occurs
        logger.error("Request ID %s: HTTP request failed: %s", unique_id, e)
        raise RuntimeError("Request failed: %s" % e) from e

    # Attempt to parse the response as JSON
    try:
        data = response.json()
        logger.debug("Request ID %s: Response JSON: %s", unique_id, data)
        return data
    except json.JSONDecodeError:
        # Log and raise a value error if the response content is not valid JSON
        logger.error("Request ID %s: Failed to decode JSON from response", unique_id)
        raise ValueError("Response content is not valid JSON")

def fetch_json_get(url, headers, unique_id, timeout=5):
    """
    Sends a GET request to the specified URL with the provided headers,
    and returns the response parsed as JSON.

    Args:
        url (str): The API endpoint to send the GET request to.
        headers (dict): HTTP headers to include in the request.
        unique_id (str): A unique identifier for this request, used in logging for traceability.
        timeout (int): Maximum time to wait for a response, in seconds. Defaults to 5.

    Returns:
        dict: The JSON-parsed response from the server.

    Raises:
        RuntimeError: If the request encounters an HTTP error or connection issue.
        ValueError: If the response body is not valid JSON.
    """
    try:
        # Log the start of the request
        logger.info("Request ID %s: Requesting response from %s", unique_id, url)
        
        # Send GET request
        response = requests.get(url, headers=headers, timeout=timeout)
        
        # Raise an error for bad HTTP status codes (4xx, 5xx)
        response.raise_for_status()
        logger.info("Request ID %s: Received response with status code %d", unique_id, response.status_code)

    except requests.exceptions.RequestException as e:
        # Log and raise a runtime error for any request issues
        logger.error("Request ID %s: HTTP request failed: %s", unique_id, e)
        raise RuntimeError("Request failed: %s" % e) from e

    try:
        # Parse and return JSON data
        data = response.json()
        logger.debug("Request ID %s: Response JSON: %s", unique_id, data)
        return data

    except json.JSONDecodeError:
        # Log and raise an error if the response is not valid JSON
        logger.error("Request ID %s: Failed to decode JSON from response", unique_id)
        raise ValueError("Response content is not valid JSON")

def get_bdo_bearer_header(unique_id):
    """
    Generates the bearer token required to authenticate with the BDO Deals API
    and constructs a headers dictionary containing the token.

    Args:
        unique_id (str): A unique identifier used for logging and traceability.

    Returns:
        dict: A dictionary of headers including the bearer token for authenticated requests.
    """
    # Endpoint to fetch the bearer token
    url = "https://www.deals.bdo.com.ph/v4/oauth/token"

    # HTTP headers for the token request
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://www.deals.bdo.com.ph",
        "Referer": "https://www.deals.bdo.com.ph",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        )
    }

    # Payload with required authentication fields
    payload = {
        "url": "www.deals.bdo.com.ph",
        "identifier": "ac5d0ec8cf6a28ae2b72411d5c95307f"
    }

    # Call utility function to send POST request and get the bearer token
    bearer_token = fetch_json_post(url, headers, payload, unique_id, timeout=5)

    # Prepare headers that include the retrieved bearer token
    bearer_headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {bearer_token.get('bearer_token')}",
        "Origin": "https://www.deals.bdo.com.ph",
        "Referer": "https://www.deals.bdo.com.ph",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
        )
    }

    return bearer_headers

def get_bdo_promo_categories(unique_id, headers):
    """
    Fetches the list of promo category IDs from deals.bdo.com.ph via the PerxTech API.

    Args:
        unique_id (str): A unique identifier used for logging and traceability.
        headers (dict): HTTP headers including the required Authorization bearer token.

    Returns:
        dict: A dictionary containing the UUID and a list of category IDs.

    Raises:
        ValueError: If no category IDs are found in the response.
    """
    # API endpoint to fetch promo categories
    url = "https://api.perxtech.net/v4/categories"

    # Make a GET request to the categories endpoint
    data = fetch_json_get(url, headers, unique_id, timeout=5)

    # Extract category IDs from the response
    ids = [item["id"] for item in data.get("data", []) if "id" in item]

    # Handle case where no IDs are returned
    if not ids:
        logger.error("Request ID %s: IDs not found in response JSON: %s", unique_id, ids)
        raise ValueError("IDs not found in response JSON: %s" % ids)

    logger.info("Request ID %s: Category IDs successfully retrieved", unique_id)

    # Return result as a dictionary
    return {
        "uuid": unique_id,
        "categories": ids
    }

def get_bdo_promo_items(unique_id, headers):
    """
    Retrieves a list of promo items from deals.bdo.com.ph, categorized by item type.

    This function:
    - Gets all promo category IDs via the PerxTech API
    - For each category, determines how many pages of items exist
    - Iterates through each page and collects all item_type/item_id pairs
    - Separates and returns items into Campaign and Reward::Campaign types

    Args:
        unique_id (str): A unique identifier used for logging and traceability.
        headers (dict): HTTP headers including the Authorization bearer token.

    Returns:
        tuple: A tuple containing:
            - campaign_list (list of tuples): List of (item_type, item_id) for type 'Campaign'
            - reward_list (list of tuples): List of (item_type, item_id) for type 'Reward::Campaign'
    """
    category_ids = get_bdo_promo_categories(unique_id, headers).get('categories')
    page_size = 50
    url_template = "https://api.perxtech.net/v4/catalogs/1/items?page={}&size={}&category_ids={}"

    all_items = []

    # Loop through each category to fetch all paginated items
    for category_id in category_ids:
        # First request to determine total pages
        url = url_template.format(1, page_size, category_id)
        data = fetch_json_get(url, headers, unique_id, timeout=5)

        try:
            pages = data.get("meta", {}).get("total_pages", 0)
            logger.info("Request ID %s: Extracting %s pages for category_id=%s", unique_id, pages, category_id)
        except (KeyError, TypeError, ValueError) as e:
            logger.error("Request ID %s: Failed to extract total_pages: %s", unique_id, e)
            continue

        # Loop through each page to gather items
        for page_num in range(1, pages + 1):
            url = url_template.format(page_num, page_size, category_id)
            data = fetch_json_get(url, headers, unique_id, timeout=5)

            items = [
                (item.get('item_type'), item.get('item_id'))
                for item in data.get('data', [])
                if item.get('item_type') and item.get('item_id')
            ]
            all_items.extend(items)

            logger.info("Request ID %s: Retrieved %d items from page %d (category_id=%s)", unique_id, len(items), page_num, category_id)

            # Random delay to avoid rate limiting
            time.sleep(random.uniform(1, 5))

    # Separate items based on type
    campaign_list = [item for item in all_items if item[0] == 'Campaign']
    reward_list = [item for item in all_items if item[0] == 'Reward::Campaign']

    logger.info("Request ID %s: Retrieved %d campaigns and %d rewards", unique_id, len(campaign_list), len(reward_list))

    return campaign_list, reward_list

def get_bdo_campaign_details(unique_id, headers, campaign_list):
    """
    Retrieves detailed information for each campaign in the given list.

    Args:
        unique_id (str): Unique identifier for logging and tracing.
        headers (dict): HTTP headers including Authorization token.
        campaign_list (list of tuples): List of (item_type, item_id) tuples where item_type should be 'Campaign'.

    Returns:
        list: A list of dictionaries, each containing detailed campaign information.
    """
    data_set = []

    for _, campaign_id in campaign_list:
        camp_url = f"https://api.perxtech.net/v4/campaigns/{campaign_id}"
        try:
            data = fetch_json_get(camp_url, headers, unique_id)
        except Exception as e:
            logger.error("Request ID %s: Failed to fetch campaign %s details: %s", unique_id, campaign_id, e)
            continue
        
        time.sleep(random.uniform(1, 5))  # Use uniform for smoother delay
        
        json_data = data.get('data', {})

        output = {
            "id": json_data.get("id"),
            "name": json_data.get("name"),
            "headline": json_data.get("display_properties", {}).get("landing_page", {}).get("headline"),
            "sub_headline": json_data.get("display_properties", {}).get("landing_page", {}).get("sub_headline"),
            "body_text": json_data.get("display_properties", {}).get("landing_page", {}).get("body_text"),
            "enrolment_page_body_text": json_data.get("display_properties", {}).get("enrolment_page", {}).get("body_text"),
            "additional_sections": json_data.get("display_properties", {}).get("landing_page", {}).get("additional_sections", []),
            "link": f"https://www.deals.bdo.com.ph/treat-welcome/{campaign_id}"
        }

        data_set.append(output)

    return data_set

def get_bdo_reward_details(unique_id, headers, reward_list):
    """
    Retrieves detailed information for each reward in the given list,
    including flattened accordion sections.

    Args:
        unique_id (str): Unique identifier for logging and tracing.
        headers (dict): HTTP headers including Authorization token.
        reward_list (list of tuples): List of (item_type, item_id) tuples where item_type should be 'Reward::Campaign'.

    Returns:
        list: A list of dictionaries, each containing detailed reward information with flattened accordions.
    """
    data_set = []

    for _, reward_id in reward_list:
        reward_url = f"https://api.perxtech.net/v4/rewards/{reward_id}"
        try:
            data = fetch_json_get(reward_url, headers, unique_id)
        except Exception as e:
            logger.error("Request ID %s: Failed to fetch reward %s details: %s", unique_id, reward_id, e)
            continue

        time.sleep(random.uniform(1, 5))  # smoother random delay

        json_data = data.get('data', {})

        result = {
            "id": json_data.get("id"),
            "name": json_data.get("name"),
            "description": json_data.get("description"),
        }

        # Flatten accordions into indexed keys
        accordions = (json_data or {}).get("accordions") or []
        for idx, accordion in enumerate(accordions, start=1):
            try:
                result[f"accordion_{idx}_title"] = accordion.get("title", "")
                result[f"accordion_{idx}_body"] = accordion.get("body", "")
            except AttributeError:
                # accordion is likely None or not a dict
                result[f"accordion_{idx}_title"] = ""
                result[f"accordion_{idx}_body"] = ""

        data_set.append(result)

    return data_set

def parse_bdo_campaign_output(raw_data: List[dict], unique_id:str) -> List[dict]:
    """
    Parses BDO campaign output into a flattened list of promo dictionaries.

    Args:
        raw_data (List[dict]): Raw data from get_bdo_campaign_details()
        unique_id (str): UUID for the scrape

    Returns:
        List[dict]: Parsed data with promo_url, promo_content, bank_name, and scrape_date.
    """
    parsed_promos = []

    for entry in raw_data:
        # Extract & clean all relevant fields
        fields = [
            entry.get("name", ""),
            entry.get("headline", ""),
            entry.get("sub_headline", ""),
            html_to_text(entry.get("body_text", "")),
            html_to_text(entry.get("enrolment_page_body_text", ""))
        ]

        # Add additional sections (if any)
        for sec in entry.get("additional_sections", []):
            if isinstance(sec, dict):
                fields.append(html_to_text(sec.get("body_text", "")))

        # Join all content parts cleanly
        promo_content = "\n\n".join([part for part in fields if part.strip()])

        parsed_promos.append(
            BankPromo(
                scrape_id = unique_id,
                bank_name="bdo",
                promo_url=f"https://www.deals.bdo.com.ph/rewards/{entry.get('id')}",
                promo_content=promo_content,
                scrape_date=date.today()
            )
        )

    return parsed_promos

def parse_bdo_reward_output(raw_data: List[dict], unique_id:str) -> List[dict]:
    """
    Parses BDO reward data into a consistent flat promo schema.

    Args:
        raw_data (List[dict]): Raw data from get_bdo_reward_details()
        unique_id (str): UUID for the scrape

    Returns:
        List[dict]: Parsed reward data with standard fields:
            - bank_name
            - promo_url (synthetic)
            - promo_content (cleaned + concatenated)
            - scrape_date
    """
    parsed_promos = []

    for entry in raw_data:
        # Extract & clean primary fields
        fields = [
            entry.get("name", ""),
            html_to_text(entry.get("description", ""))
        ]

        # Extract and clean accordion fields
        idx = 1
        while f"accordion_{idx}_body" in entry:
            title = entry.get(f"accordion_{idx}_title", "")
            body = html_to_text(entry.get(f"accordion_{idx}_body", ""))
            if title or body:
                fields.append(f"{title}\n{body}".strip())
            idx += 1

        # Join all text into one content block
        promo_content = "\n\n".join([part for part in fields if part.strip()])

        parsed_promos.append(
            BankPromo(
                scrape_id = unique_id,
                bank_name="bdo",
                promo_url=f"https://www.deals.bdo.com.ph/rewards/{entry.get('id')}",
                promo_content=promo_content,
                scrape_date=date.today()
            )
        )

    return parsed_promos

def scrape_bdo():
    """
    Scrapes promotional data from BDO's campaigns and rewards endpoints, parses the outputs,
    and returns them in a unified format.

    Returns:
        List[dict]: A list of standardized promo entries from BDO, combining campaign and reward data.
    """
    scrape_id = str(uuid.uuid4())
    logger.info("Starting BDO scrape with ID: %s", scrape_id)

    # Get bearer token for API access
    bearer_token = get_bdo_bearer_header(scrape_id)
    logger.info("Retrieved BDO bearer token.")

    # Get campaign and reward item references
    campaigns, rewards = get_bdo_promo_items(scrape_id, bearer_token)
    logger.info("Retrieved %d campaigns and %d rewards", len(campaigns), len(rewards))

    # Fetch detailed content
    campaign_data = get_bdo_campaign_details(scrape_id, bearer_token, campaigns)
    reward_data = get_bdo_reward_details(scrape_id, bearer_token, rewards)
    logger.info("Fetched detailed data for campaigns and rewards")

    # Parse into flat schema
    campaign_promos = parse_bdo_campaign_output(campaign_data, scrape_id)
    reward_promos = parse_bdo_reward_output(reward_data, scrape_id)
    logger.info("Parsed campaigns (%d) and rewards (%d) into unified format", len(campaign_promos), len(reward_promos))

    # Merge
    all_promos = campaign_promos + reward_promos
    logger.info("Merged total BDO promos: %d", len(all_promos))

    return all_promos