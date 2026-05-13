import requests
from bs4 import BeautifulSoup
import json
import logging
from .registry import SBI_MF_URLS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class GrowwScraper:
    """
    Scraper specialized for Groww.in Mutual Fund pages.
    Extracts key financial data points like NAV, Risk, and Fund Objective.
    """
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def scrape_fund(self, url: str):
        """Scrapes a single fund page and returns structured data."""
        try:
            logger.info(f"Fetching: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Note: Selectors may need adjustment based on Groww's live DOM
            # These are representative selectors for common financial sites
            data = {
                "url": url,
                "fund_name": soup.find('h1').text.strip() if soup.find('h1') else "N/A",
                "nav": self._extract_nav(soup),
                "objective": self._extract_objective(soup),
                "risk": self._extract_risk(soup)
            }
            
            return data
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return None

    def _extract_nav(self, soup):
        # Implementation depends on exact DOM structure
        # Common pattern: Search for text 'NAV' or a specific class
        nav_tag = soup.find(string=lambda t: 'NAV' in t and '(' not in t)
        return nav_tag.parent.find_next_sibling().text if nav_tag and nav_tag.parent else "N/A"

    def _extract_objective(self, soup):
        obj_tag = soup.find(string=lambda t: 'Investment Objective' in t)
        return obj_tag.parent.find_next_sibling().text if obj_tag and obj_tag.parent else "N/A"

    def _extract_risk(self, soup):
        risk_tag = soup.find(string=lambda t: 'Risk' in t)
        return risk_tag.parent.text if risk_tag else "N/A"

def run_phase0():
    """Executes the Phase 0 data sourcing task."""
    scraper = GrowwScraper()
    results = []
    
    logger.info("Starting Phase 0: Data Sourcing (Exclusive URLs)")
    for url in SBI_MF_URLS:
        fund_data = scraper.scrape_fund(url)
        if fund_data:
            results.append(fund_data)
    
    # Save results for Phase 1
    with open("phase0_data.json", "w") as f:
        json.dump(results, f, indent=4)
    
    logger.info(f"Phase 0 Complete. Scraped {len(results)} funds.")

if __name__ == "__main__":
    run_phase0()
