"""CyberGuard-ID — Security Components (STRIDE).

Implements API Key authentication, Audit Logging, Security Headers,
and Payload size limiting to ensure application security even in local environments.
"""

from __future__ import annotations

import json
import logging
import secrets
import time
from collections import defaultdict
from pathlib import Path
from typing import Callable

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware

# Generate a single API key per runtime session for local security (Spoofing prevention)
RUNTIME_API_KEY = secrets.token_urlsafe(32)

# Audit logger setup (Repudiation prevention)
AUDIT_LOG_FILE = Path("artifacts") / "audit.log"
AUDIT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)
# Remove all handlers to avoid duplicate logs in the console
if audit_logger.hasHandlers():
    audit_logger.handlers.clear()

file_handler = logging.FileHandler(str(AUDIT_LOG_FILE), encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
audit_logger.addHandler(file_handler)
# Disable propagation so it doesn't pollute the main stdout logger
audit_logger.propagate = False

MAX_PAYLOAD_SIZE = 10 * 1024 * 1024  # 10 MB limit (Denial of Service prevention)

# Simple in-memory rate limiting state
_rate_limits: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60  # seconds


def verify_api_key(request: Request) -> None:
    """Dependency to verify API Key on protected routes."""
    # We check headers for the X-API-Key
    api_key = request.headers.get("X-API-Key")
    
    # We also allow it to be passed via query params for SSE/EventSource which can't send headers easily
    if not api_key:
        api_key = request.query_params.get("api_key")
        
    if not api_key or api_key != RUNTIME_API_KEY:
        audit_logger.warning(
            f"AUTH_FAILURE | IP: {request.client.host if request.client else 'unknown'} "
            f"| Method: {request.method} | Path: {request.url.path} | Key provided: {'Yes' if api_key else 'No'}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key. Access denied by STRIDE Security Policy.",
        )


class SecurityMiddleware(BaseHTTPMiddleware):
    """Handles Security Headers, Audit Logging, and Size Limits."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # --- 1. Audit Logging: Pre-request info
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        
        # --- 2. Denial of Service: Simple Rate Limiting (per IP)
        now = time.time()
        _rate_limits[client_ip] = [t for t in _rate_limits[client_ip] if now - t < RATE_LIMIT_WINDOW]
        if len(_rate_limits[client_ip]) >= RATE_LIMIT_REQUESTS:
            audit_logger.warning(f"RATE_LIMIT | IP: {client_ip} | Method: {method} | Path: {path}")
            return Response(
                json.dumps({"detail": "Rate Limit Exceeded. Max 100 requests per minute."}),
                status_code=429,
                media_type="application/json"
            )
        _rate_limits[client_ip].append(now)

        # --- 3. Denial of Service: Payload Size Limit
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_PAYLOAD_SIZE:
            audit_logger.warning(f"PAYLOAD_TOO_LARGE | IP: {client_ip} | Size: {content_length} bytes")
            return Response(
                json.dumps({"detail": "Payload Too Large. Limit is 10MB."}),
                status_code=413,
                media_type="application/json"
            )

        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            process_time = (time.time() - start_time) * 1000
            
            # --- 4. Tampering & Info Disclosure: Security Headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            # Prevent caching of API responses to avoid stale sensitive data leakage
            if path.startswith("/api/"):
                response.headers["Cache-Control"] = "no-store, max-age=0"
                
            # Log successful/handled request
            # Exclude noisy endpoints like progress streaming or static files from flooding the audit log
            if not path.startswith("/static/") and "/progress" not in path:
                audit_logger.info(
                    f"AUDIT | IP: {client_ip} | Method: {method} | Path: {path} | "
                    f"Status: {response.status_code} | Time: {process_time:.2f}ms"
                )
            return response
            
        except Exception as e:
            # Log unhandled exceptions (Information Disclosure prevention)
            audit_logger.error(
                f"ERROR | IP: {client_ip} | Method: {method} | Path: {path} | "
                f"Exception: {str(e)}"
            )
            raise
