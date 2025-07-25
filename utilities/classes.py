from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import date

class BankPromo(BaseModel):
    scrape_id: str
    bank_name: str
    promo_url: HttpUrl
    promo_content: str
    scrape_date: date
