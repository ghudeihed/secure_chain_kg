import sys
import os
import time
import logging
import json
from enum import Enum
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from converters.json_converter import JsonConverter
from converters.spdx_converter import SpdxConverter
from converters.cyclonedx_converter import CycloneDXConverter
from app.sbom_generator import SbomGenerator
from app.sparql_client import SparqlClient

# Add parent directory to sys.path to resolve app and converters modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging with detailed format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SBOM Generator API",
    description="API for generating Software Bills of Materials (SBOMs) from a Secure Chain Knowledge Graph",
    version="1.0.0"
)

# CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory rate limiting store
rate_limit_store = {}

# Get configuration from environment with defaults
SPARQL_ENDPOINT = os.getenv("SPARQL_ENDPOINT", "http://fuseki:3030/securechain/query")
CACHE_EXPIRY = int(os.getenv("CACHE_EXPIRY", "600"))

# Create SPARQL client
sparql_client = SparqlClient(SPARQL_ENDPOINT, CACHE_EXPIRY)

# Enum for format field
class SbomFormat(str, Enum):
    JSON = "json"
    SPDX = "spdx"
    CYCLONEDX = "cyclonedx"

# Root endpoint (excluded from Swagger UI)
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    logger.info("Root endpoint accessed")
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SBOM Generator API</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 40px;
                line-height: 1.6;
            }
            h1 {
                color: #333;
            }
            a {
                color: #0066cc;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>SBOM Generator API</h1>
            <p>Welcome to the SBOM Generator API (v1.0.0).</p>
            <p>This API generates Software Bills of Materials (SBOMs) from a Secure Chain Knowledge Graph.</p>
            <h2>API Resources</h2>
            <ul>
                <li><a href="/docs">Swagger UI Documentation</a> - Interactive API documentation</li>
                <li><a href="/redoc">ReDoc Documentation</a> - Alternative API documentation</li>
                <li><a href="/openapi.json">OpenAPI JSON Schema</a> - Raw API specification</li>
            </ul>
            <h2>Endpoints</h2>
            <ul>
                <li><code>POST /api/sbom/generate</code> - Generate an SBOM for a software component</li>
                <li><code>GET /health</code> - Check API health status</li>
            </ul>
            <p>For more details, explore the documentation links above.</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Rate limiting middleware
@app.middleware("http")
async def rate_limit(request: Request, call_next):
    client_ip = request.client.host
    current_time = time.time()
    logger.debug(f"Processing request from IP: {client_ip}, Path: {request.url.path}")

    # Allow 100 requests per minute per IP
    if client_ip in rate_limit_store:
        # Clean up timestamps older than 1 minute
        rate_limit_store[client_ip] = [t for t in rate_limit_store[client_ip] if current_time - t < 60]
        if len(rate_limit_store[client_ip]) >= 100:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}, request count: {len(rate_limit_store[client_ip])}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."}
            )
    else:
        rate_limit_store[client_ip] = []

    rate_limit_store[client_ip].append(current_time)
    response = await call_next(request)
    return response

# SBOM generation endpoint
@app.post(
    "/api/sbom/generate",
    summary="Generate Software Bill of Materials",
    description="Generates an SBOM for a specified software component in the requested format (JSON, SPDX, or CycloneDX). Provide the software name and desired output format as form data."
)
async def generate_sbom(
    software_name: str = Form(
        ...,
        description="The name of the software component (e.g., 'nginx', 'apache'). Must be a non-empty string containing alphanumeric characters, dots, hyphens, or underscores."
    ),
    format: SbomFormat = Form(
        ...,
        description="The output format for the SBOM. Choose one of: 'json', 'spdx', or 'cyclonedx'.",
        examples=["json"]
    )
):
    logger.info(f"Received SBOM generation request: software_name={software_name}, format={format}")

    # Validate input
    if not software_name.strip():
        logger.error("Software name is empty or contains only whitespace")
        raise HTTPException(status_code=400, detail="Software name cannot be empty or whitespace")

    if format not in ["json", "spdx", "cyclonedx"]:
        logger.error(f"Invalid format specified: {format}")
        raise HTTPException(status_code=400, detail="Invalid format. Must be 'json', 'spdx', or 'cyclonedx'")

    try:
        # Generate SBOM
        logger.debug(f"Initializing SbomGenerator for {software_name}")
        sbom_generator = SbomGenerator(sparql_client)
        logger.debug(f"Generating SBOM for {software_name}")
        start_time = time.time()
        sbom = sbom_generator.generate_sbom(software_name)
        logger.info(f"SBOM generated successfully in {time.time() - start_time:.2f}s")

        # Convert to requested format
        logger.debug(f"Converting SBOM to format: {format}")
        if format == "json":
            converter = JsonConverter()
        elif format == "spdx":
            converter = SpdxConverter()
        elif format == "cyclonedx":
            converter = CycloneDXConverter()

        result = converter.convert(sbom)
        logger.debug("SBOM conversion completed")

        # Return the formatted SBOM
        return JSONResponse(content=json.loads(result))
    except ValueError as e:
        logger.error(f"Validation error during SBOM generation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error generating SBOM for {software_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating SBOM")

# Health check endpoint
@app.get("/health")
async def health_check():
    logger.info("Health check requested")
    return {"status": "healthy"}

# Run the application
if __name__ == "__main__":
    logger.info("Starting FastAPI application")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )