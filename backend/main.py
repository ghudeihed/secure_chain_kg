import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import uvicorn
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SBOM Generator API",
    description="API for generating Software Bills of Materials (SBOMs) from a Secure Chain Knowledge Graph",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# Jinja2 templates
templates = Jinja2Templates(directory="./templates")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}", exc_info=True)
    return {"detail": "Internal server error"}, 500

# Root endpoint
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root(request: Request):
    try:
        logger.info(f"Root endpoint accessed by {request.client.host}")
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering root endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to render page")

# Placeholder for SBOM generation endpoint
@app.post("/api/sbom/generate")
async def generate_sbom():
    """
    Generate an SBOM for a software component.
    (Implementation pending)
    """
    logger.info("SBOM generation endpoint accessed")
    raise HTTPException(status_code=501, detail="Endpoint not implemented")

# Placeholder for health check endpoint
@app.get("/health")
async def health_check():
    """
    Check API health status.
    Returns a simple status message.
    """
    logger.info("Health check endpoint accessed")
    return {"status": "healthy"}

# Run the application
if __name__ == "__main__":
    logger.info("Starting FastAPI application")
    # For development, prefer: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info",
        reload=True,
        reload_dirs=["./", "templates"]
    )