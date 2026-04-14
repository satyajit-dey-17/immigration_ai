import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta, timezone
from scrapy.spiders import SitemapSpider
from pipeline import ingest_page


class USCISDailySpider(SitemapSpider):
    name = "uscis_daily"
    topic = "USCIS"

    sitemap_urls = ["https://www.uscis.gov/sitemap.xml"]

    # Follow sub-sitemaps (?page=1 through ?page=5)
    sitemap_follow = [r"sitemap\.xml\?page="]

    # Only crawl immigration-relevant sections, skip PDFs and Spanish pages
    sitemap_rules = [
        (r"/es/", None),                              # skip Spanish pages
        (r"\.pdf$", None),                            # skip PDFs
        (r"/policy-manual", "parse"),
        (r"/forms", "parse"),
        (r"/green-card", "parse"),
        (r"/working-in-the-united-states", "parse"),
        (r"/citizenship", "parse"),
        (r"/humanitarian", "parse"),
        (r"/family", "parse"),
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
        "CONCURRENT_REQUESTS": 16,
        "ROBOTSTXT_OBEY": True,
        "USER_AGENT": (
            "ImmigrationIQ-Bot/1.0 "
            "(educational RAG project; respectful crawler)"
        ),
    }

    def sitemap_filter(self, entries):
        cutoff = datetime.now(timezone.utc) - timedelta(days=1)
        for entry in entries:
            lastmod = entry.get("lastmod", "")
            if not lastmod:
                yield entry   # no date = always include
                continue
            try:
                # Parse timezone-aware datetime e.g. "2026-04-06T14:15:24-04:00"
                page_date = datetime.fromisoformat(lastmod)
                if page_date >= cutoff:
                    yield entry
            except ValueError:
                yield entry   # unparseable = always include

    def parse(self, response):
        raw_text = " ".join(
            response.css("main *::text, article *::text, .content *::text")
            .getall()
        ).strip()

        if raw_text:
            ingest_page(url=response.url, raw_text=raw_text, topic=self.topic)