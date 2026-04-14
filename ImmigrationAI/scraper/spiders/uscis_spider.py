import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scrapy
from pipeline import ingest_page


class USCISSpider(scrapy.Spider):
    name = "uscis"
    topic = "USCIS"

    start_urls = [
        "https://www.uscis.gov/policy-manual",
        "https://www.uscis.gov/forms",
        "https://www.uscis.gov/green-card",
        "https://www.uscis.gov/working-in-the-united-states",
        "https://www.uscis.gov/citizenship",
        "https://www.uscis.gov/humanitarian",
        "https://www.uscis.gov/family",
        "https://travel.state.gov/content/travel/en/us-visas.html",
        "https://travel.state.gov/content/travel/en/us-visas/visa-information-resources/all-visa-categories.html",
        "https://travel.state.gov/content/travel/en/us-visas/work/temporary-worker-visas.html",
        "https://travel.state.gov/content/travel/en/us-visas/visa-information-resources/wait-times.html",
    ]

    JS_REQUIRED_DOMAINS = ["travel.state.gov"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
        "CONCURRENT_REQUESTS": 16,
        "ROBOTSTXT_OBEY": True,
        "DEPTH_LIMIT": 3,
        "USER_AGENT": (
            "ImmigrationIQ-Bot/1.0 "
            "(educational RAG project; respectful crawler)"
        ),
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000,
    }

    def _needs_js(self, url: str) -> bool:
        return any(domain in url for domain in self.JS_REQUIRED_DOMAINS)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={"playwright": self._needs_js(url)},
                callback=self.parse,
            )

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
                yield response.follow(
                    href,
                    meta={"playwright": self._needs_js(response.urljoin(href))},
                    callback=self.parse,
                )