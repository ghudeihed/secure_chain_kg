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

print("FastAPI app Initialized")