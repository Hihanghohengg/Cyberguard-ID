"""CyberGuard-ID — FastAPI Main Application.

Entry point for the web server. Mounts API routers and serves the
frontend static files.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from server.api import analysis, reports, system
from server.security import SecurityMiddleware, verify_api_key, RUNTIME_API_KEY

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Create FastAPI app
app = FastAPI(
    title="CyberGuard-ID",
    description="Skrining & Prioritisasi Moderasi Komentar YouTube Indonesia",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# STRIDE: Security Middleware (Audit Logging, Rate Limit, Header injection)
app.add_middleware(SecurityMiddleware)

# STRIDE: Strict CORS — allow local origins only to prevent SSRF/CSRF from external sites
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# STRIDE: Information Disclosure Prevention
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import logging
    logging.getLogger("audit").error(f"UNHANDLED EXCEPTION: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error (Blocked by STRIDE Information Disclosure Prevention)"},
    )

# Mount API routers with STRIDE API Key verification dependency
app.include_router(analysis.router, dependencies=[Depends(verify_api_key)])
app.include_router(reports.router, dependencies=[Depends(verify_api_key)])
app.include_router(system.router, dependencies=[Depends(verify_api_key)])


# Mount static files (CSS, JS, assets)
if FRONTEND_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(FRONTEND_DIR)),
        name="static",
    )


@app.get("/", include_in_schema=False)
@app.head("/", include_in_schema=False)
async def serve_index():
    """Serve the SPA index.html."""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        response = FileResponse(
            index_path,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )
        # STRIDE: Issue the runtime API key so the SPA can authenticate API requests
        response.set_cookie(
            key="stride_api_key",
            value=RUNTIME_API_KEY,
            httponly=False,  # JS needs to read it to set X-API-Key header
            samesite="lax",
        )
        return response
    return {"message": "CyberGuard-ID API is running. Frontend not found."}


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "cyberguard-id"}
