import json
import os
import logging
from typing import List, Dict

# Attempt to use real scraper, fallback to mock if requested or in restricted environment
try:
    from src.phase0_data_sourcing.scraper import GrowwScraper
except ImportError:
    from src.phase0_data_sourcing.mock_scraper import GrowwScraper

from src.phase0_data_sourcing.registry import SBI_MF_URLS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class DataAcquisition:
    """
    Handles Phase 1.1: Data Acquisition & Validation.
    """
    
    def __init__(self, output_dir: str = "src/phase1_ingestion/data"):
        # Use mock scraper for this demonstration environment
        try:
            from src.phase0_data_sourcing.mock_scraper import GrowwScraper as MockScraper
            self.scraper = MockScraper()
            logger.info("Using MOCK scraper for environment compatibility.")
        except ImportError:
            self.scraper = GrowwScraper()
            
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def run(self):
        """Executes the acquisition and cleaning process."""
        logger.info("Starting Phase 1.1: Data Acquisition & Validation")
        
        acquired_data = []
        
        for url in SBI_MF_URLS:
            raw_data = self.scraper.scrape_fund(url)
            
            if raw_data and self._validate(raw_data):
                cleaned_data = self._clean(raw_data)
                acquired_data.append(cleaned_data)
                logger.info(f"Successfully acquired and cleaned: {cleaned_data['fund_name']}")
            else:
                logger.warning(f"Validation failed or data missing for: {url}")

        output_path = os.path.join(self.output_dir, "cleaned_funds.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(acquired_data, f, indent=4)
        
        logger.info(f"Phase 1.1 Complete. Saved {len(acquired_data)} funds to {output_path}")

    def _validate(self, data: Dict) -> bool:
        required_fields = ["fund_name", "nav", "objective"]
        for field in required_fields:
            if not data.get(field) or data[field] == "N/A":
                return False
        return True

    def _clean(self, data: Dict) -> Dict:
        data["fund_name"] = data["fund_name"].strip()
        # Handle cases where NAV might already be a float or string with currency
        nav_str = str(data["nav"])
        data["nav"] = nav_str.replace("NAV as of", "").replace("₹", "").strip()
        data["objective"] = data["objective"].strip()
        data["status"] = "cleaned"
        data["version"] = "1.1"
        return data

if __name__ == "__main__":
    acquisition = DataAcquisition()
    acquisition.run()
