import uvicorn
from src.phase3_backend.app import app

# Expose the FastAPI app for deployment platforms auto-detection
# (e.g. Render, Hugging Face Spaces, Deta, etc.)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
