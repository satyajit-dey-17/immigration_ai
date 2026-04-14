import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scrapy
from pipeline import ingest_page


class EVerifySpider(scrapy.Spider):
    name = "everify"
    topic = "E-Verify"

    start_urls = [
        "https://www.e-verify.gov/employers/employer-resources",
        "https://www.e-verify.gov/employees/employee-rights-and-responsibilities",
        "https://www.e-verify.gov/about-e-verify/e-verify-overview",
        "https://www.uscis.gov/i-9-central",
        "https://www.uscis.gov/i-9-central/form-i-9-acceptable-documents",
        "https://www.uscis.gov/i-9-central/complete-correct-form-i-9",
        "https://www.uscis.gov/i-9-central/i-9-resources",
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