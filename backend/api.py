"""
FastAPI application for the SBOM Construction Tool.
"""
from models import (
    SoftwareInfo,
    VersionInfo,
    DependencyInfo,
    SBOMRequest,
    SBOMResponse,
    VulnerabilityInfo,
    LicenseInfo,
    MetadataInfo,
)
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI app
app = FastAPI(
    title="SBOM Construction Tool API",
    description="API for generating Software Bill of Materials (SBOM) from the Secure Chain Knowledge Graph",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to the SBOM Construction Tool API"}

# Run the application
if __name__ == "__main__":
    import uvicorn
    from config import API_HOST, API_PORT
    
    uvicorn.run("api:app", host=API_HOST, port=API_PORT, reload=True)