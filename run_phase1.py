import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_pipeline():
    steps = [
        "src.phase1_ingestion.subphase_1_1.acquisition",
        "src.phase1_ingestion.subphase_1_2.transformation",
        "src.phase1_ingestion.subphase_1_3.embeddings",
        "src.phase1_ingestion.subphase_1_4.indexing"
    ]
    
    for step in steps:
        logger.info(f"--- Running {step} ---")
        result = subprocess.run(["python", "-m", step], capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Failed at {step}:\n{result.stderr}")
            break
        else:
            logger.info(f"Success:\n{result.stdout}")

if __name__ == "__main__":
    run_pipeline()
