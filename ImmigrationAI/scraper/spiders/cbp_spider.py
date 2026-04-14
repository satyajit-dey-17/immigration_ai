import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scrapy
from pipeline import ingest_page


class CBPSpider(scrapy.Spider):
    name = "cbp"
    topic = "CBP"

    start_urls = [
        "https://www.cbp.gov/travel/international-visitors",
        "https://www.cbp.gov/travel/international-visitors/visa-waiver-program",
        "https://www.cbp.gov/travel/international-visitors/esta",
        "https://www.cbp.gov/travel/international-visitors/kiosk",
        "https://www.cbp.gov/travel/us-citizens/i-94-central",
        "https://www.cbp.gov/travel/international-visitors/i-94-instructions",
        "https://www.cbp.gov/travel/international-visitors/admissibility",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "ROBOTSTXT_OBEY": True,
        "DEPTH_LIMIT": 2,
        "USER_AGENT": (
            "ImmigrationIQ-Bot/1.0 "
            "(educational RAG project; respectful crawler)"
        ),
    }

    def parse(self, response):
        raw_text = " ".join(
            response.css("main *::text, article *::text, .content *::text")
            .getall()
        ).strip()

        if raw_text:
            ingest_page(url=response.url, raw_text=raw_text, topic=self.topic)

        skip = ["/es/", "javascript:", "#", ".pdf", ".xls", "/logout"]
        for href in response.css("a::attr(href)").getall():
            if href and href.startswith("/") and not any(s in href for s in skip):
                yield response.follow(href, callback=self.parse)