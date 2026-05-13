from fastapi.testclient import TestClient
from src.phase3_backend.app import app
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

client = TestClient(app)

def test_chat_api():
    logger.info("--- Testing Phase 3 API ---")
    
    # Test 1: Valid Query (Should return answer and citation)
    logger.info("Test 1: Valid Query")
    response = client.post("/api/chat", json={"query": "What is the NAV of the SBI PSU Fund?"})
    logger.info(f"Response: {response.json()}")
    
    # Test 2: Unknown Query (Should trigger Null-Citation boundary)
    logger.info("\nTest 2: Unknown Query (Testing Null-Citation Boundary)")
    # Since we are using a mock LLM that always returns a canned response for valid funds, 
    # we simulate an 'unknown' response by querying something not in the mock.
    response = client.post("/api/chat", json={"query": "What is the weather?"})
    logger.info(f"Response: {response.json()}")
    
    # Test 3: PII Rejection (Should return 400 Bad Request)
    logger.info("\nTest 3: PII Rejection Boundary")
    response = client.post("/api/chat", json={"query": "My phone number is 9876543210, what is the Gold fund NAV?"})
    logger.info(f"Status Code: {response.status_code}")
    logger.info(f"Response: {response.json()}")

if __name__ == "__main__":
    test_chat_api()
