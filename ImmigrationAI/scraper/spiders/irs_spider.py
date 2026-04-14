import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scrapy
from pipeline import ingest_page


class IRSSpider(scrapy.Spider):
    name = "irs"
    topic = "IRS"

    start_urls = [
        "https://www.irs.gov/individuals/international-taxpayers",
        "https://www.irs.gov/individuals/international-taxpayers/foreign-student-liability-for-social-security-and-medicare-taxes",
        "https://www.irs.gov/individuals/international-taxpayers/nonresident-aliens",
        "https://www.irs.gov/individuals/international-taxpayers/taxation-of-nonresident-aliens",
        "https://www.irs.gov/individuals/international-taxpayers/us-tax-treaties",
        "https://www.irs.gov/individuals/international-taxpayers/substantial-presence-test",
        "https://www.irs.gov/individuals/international-taxpayers/claiming-tax-treaty-benefits",
        "https://www.irs.gov/individuals/international-taxpayers/students-and-exchange-visitors",
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

        skip = ["/es/", "javascript:", "#", ".pdf", ".xls", "/logout", "/pub/"]
        for href in response.css("a::attr(href)").getall():
            if href and href.startswith("/") and not any(s in href for s in skip):
                yield response.follow(href, callback=self.parse)