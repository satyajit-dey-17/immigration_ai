import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scrapy
from pipeline import ingest_page


class EOIRSpider(scrapy.Spider):
    name = "eoir"
    topic = "EOIR"

    start_urls = [
        "https://www.justice.gov/eoir",
        "https://www.justice.gov/eoir/immigration-court-practice-manual",
        "https://www.justice.gov/eoir/board-of-immigration-appeals",
        "https://www.justice.gov/eoir/filing-fees",
        "https://www.justice.gov/eoir/list-pro-bono-legal-service-providers",
        "https://www.justice.gov/eoir/attorney-roster",
        "https://www.justice.gov/eoir/immigration-court-information",
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