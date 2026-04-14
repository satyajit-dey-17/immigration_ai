import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scrapy
import urllib.request
import json
from pipeline import ingest_page


class FederalRegisterSpider(scrapy.Spider):
    name = "federal_register"
    topic = "Federal Rules"

    BASE_API = (
        "https://www.federalregister.gov/api/v1/documents.json"
        "?conditions[term]=immigration"
        "&conditions[type][]=RULE"
        "&conditions[type][]=PRORULE"
        "&conditions[type][]=NOTICE"
        "&fields[]=title"
        "&fields[]=abstract"
        "&fields[]=html_url"
        "&fields[]=publication_date"
        "&fields[]=agency_names"
        "&per_page=20&order=newest"
    )

    start_urls = ["https://www.federalregister.gov"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": "ImmigrationIQ-Bot/1.0",
    }

    def start_requests(self):
        url = self.BASE_API
        page = 1

        while url:
            try:
                self.logger.info(f"Fetching Federal Register API page {page}...")
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "ImmigrationIQ-Bot/1.0"}
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode())

                results = data.get("results", [])
                self.logger.info(f"Page {page}: {len(results)} documents")

                for doc in results:
                    title    = (doc.get("title")            or "").strip()
                    abstract = (doc.get("abstract")         or "").strip()
                    html_url = (doc.get("html_url")         or "").strip()
                    pub_date = (doc.get("publication_date") or "").strip()
                    agencies = ", ".join(doc.get("agency_names") or [])

                    raw_text = "\n".join(filter(None, [
                        f"Title: {title}"        if title    else None,
                        f"Published: {pub_date}" if pub_date else None,
                        f"Agencies: {agencies}"  if agencies else None,
                        f"Summary: {abstract}"   if abstract else None,
                    ]))

                    if raw_text and html_url:
                        ingest_page(
                            url=html_url,
                            raw_text=raw_text,
                            topic=self.topic
                        )

                url = data.get("next_page_url")
                page += 1

            except Exception as e:
                self.logger.error(f"API fetch failed on page {page}: {e}")
                break

        yield scrapy.Request(
            "https://www.federalregister.gov",
            callback=self.parse,
            dont_filter=True
        )

    def parse(self, response):
        pass