import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scrapy
from pipeline import ingest_page


class DOLSpider(scrapy.Spider):
    name = "dol"
    topic = "Labor/Wage"

    start_urls = [
        "https://www.dol.gov/agencies/eta/foreign-labor",
        "https://www.dol.gov/agencies/whd/immigration",
        "https://flag.dol.gov/wage-data/wage-determinations",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "ROBOTSTXT_OBEY": True,
        "DEPTH_LIMIT": 2,
        "USER_AGENT": "ImmigrationIQ-Bot/1.0",
    }

    def parse(self, response):
        raw_text = " ".join(response.css("main *::text").getall()).strip()

        if raw_text:
            ingest_page(url=response.url, raw_text=raw_text, topic=self.topic)

        skip = ["#", ".pdf", ".xls", ".xlsx", "mailto:"]
        for href in response.css("a::attr(href)").getall():
            if href and "dol.gov" in href and not any(s in href for s in skip):
                yield response.follow(href, callback=self.parse)