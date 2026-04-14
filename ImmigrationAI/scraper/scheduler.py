import os
os.environ["PROMETHEUS_MULTIPROC_DIR"] = "/tmp/prom_multiproc"
os.makedirs("/tmp/prom_multiproc", exist_ok=True)

from dotenv import load_dotenv
load_dotenv()

import http.server
import threading
import time
from prometheus_client import (
    CollectorRegistry, multiprocess,
    generate_latest, CONTENT_TYPE_LATEST
)
from apscheduler.schedulers.background import BackgroundScheduler
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from spiders.uscis_spider import USCISSpider
from spiders.uscis_daily_spider import USCISDailySpider
from spiders.federal_register_spider import FederalRegisterSpider
from spiders.dol_spider import DOLSpider
from spiders.irs_spider import IRSSpider
from spiders.cbp_spider import CBPSpider
from spiders.eoir_spider import EOIRSpider
from spiders.visa_bulletin_spider import VisaBulletinSpider
from spiders.everify_spider import EVerifySpider


class MetricsHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)
            output = generate_latest(registry)
            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(output)
        elif self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass


def start_metrics_server():
    server = http.server.HTTPServer(("", 8001), MetricsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print("📡 Metrics server started on :8001")


def run_daily_scrape():
    print("⏰ Running daily delta scrape...")
    process = CrawlerProcess(get_project_settings())
    process.crawl(USCISDailySpider)
    process.start()
    print("✅ Daily scrape complete.")


def run_weekly_scrape():
    print("⏰ Running full weekly scrape...")
    process = CrawlerProcess(get_project_settings())
    process.crawl(USCISSpider)
    process.crawl(FederalRegisterSpider)
    process.crawl(DOLSpider)
    process.crawl(IRSSpider)
    process.crawl(CBPSpider)
    process.crawl(EOIRSpider)
    process.crawl(VisaBulletinSpider)
    process.crawl(EVerifySpider)
    process.start()
    print("✅ Weekly scrape complete.")


if __name__ == "__main__":
    start_metrics_server()

    scheduler = BackgroundScheduler()
    scheduler.add_job(run_daily_scrape, "cron", hour=2, minute=0)
    scheduler.add_job(run_weekly_scrape, "cron", day_of_week="sun", hour=3, minute=0)
    scheduler.start()

    print("📅 Scheduler running — daily at 02:00 UTC | full crawl Sundays at 03:00 UTC")

    while True:
        time.sleep(60)