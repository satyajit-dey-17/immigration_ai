import os
os.environ["PROMETHEUS_MULTIPROC_DIR"] = "/tmp/prom_multiproc"
os.makedirs("/tmp/prom_multiproc", exist_ok=True)

import sys
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


def run(mode: str = "daily"):
    settings = get_project_settings()
    process = CrawlerProcess(settings)

    if mode == "full":
        print("🕷️  Running FULL weekly crawl...")
        process.crawl(USCISSpider)
        process.crawl(FederalRegisterSpider)
        process.crawl(DOLSpider)
        process.crawl(IRSSpider)
        process.crawl(CBPSpider)
        process.crawl(EOIRSpider)
        process.crawl(VisaBulletinSpider)
        process.crawl(EVerifySpider)
    elif mode == "daily":
        print("⚡ Running DAILY delta ingest...")
        process.crawl(USCISDailySpider)
    else:
        print(f"❌ Unknown mode: {mode}. Use 'full' or 'daily'.")
        sys.exit(1)

    process.start()
    print("✅ Ingest complete.")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    run(mode)