import logging
import subprocess
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])

# Mock database for hallucination reports and analytics
mock_hallucinations = []
mock_analytics = {"total_queries": 150, "avg_latency_ms": 850, "deflection_rate": "45%"}

class HallucinationReport(BaseModel):
    query: str
    bot_answer: str
    expected_answer: str

def trigger_data_refresh():
    """Background task to run the Phase 1 ingestion pipeline."""
    logger.info("Starting background data refresh pipeline...")
    try:
        subprocess.run(["python", "run_phase1.py"], check=True)
        logger.info("Data refresh pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Data refresh pipeline failed: {e}")

@router.post("/refresh-knowledge")
async def refresh_knowledge(background_tasks: BackgroundTasks):
    """Endpoint to trigger incremental re-indexing manually from the dashboard."""
    background_tasks.add_task(trigger_data_refresh)
    return {"message": "Knowledge base refresh has been queued in the background."}

@router.get("/analytics")
async def get_analytics():
    """Returns real-time query analytics for the dashboard."""
    return mock_analytics

@router.post("/reports/hallucination")
async def report_hallucination(report: HallucinationReport):
    """Allows admins/users to manually correct 'hallucination' reports."""
    mock_hallucinations.append(report.dict())
    return {"message": "Hallucination report logged successfully for review."}

@router.get("/reports/hallucination")
async def get_hallucinations():
    """Fetch all hallucination reports."""
    return {"reports": mock_hallucinations}
