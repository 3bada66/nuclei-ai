"""HTTP security headers middleware and image magic-bytes validation."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.config import ENV

# Accepted image magic-byte signatures (offset 0)
_IMAGE_SIGNATURES: list[bytes] = [
    b"\x89PNG\r\n\x1a\n",   # PNG
    b"\xff\xd8\xff",          # JPEG
    b"II\x2a\x00",            # TIFF little-endian
    b"MM\x00\x2a",            # TIFF big-endian
    b"BM",                    # BMP
    b"GIF87a",                # GIF
    b"GIF89a",                # GIF
]


def is_valid_image_bytes(data: bytes) -> bool:
    """True iff the first bytes match a known image format signature."""
    return any(data[: len(sig)] == sig for sig in _IMAGE_SIGNATURES)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach HTTP security headers to every response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        # Prevent MIME-type sniffing attacks
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Referrer leakage control
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Disable browser features the API does not use
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=()"
        )

        if ENV == "production":
            # HSTS — only meaningful over HTTPS
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )
            # Tight CSP for a pure JSON API (docs are disabled in prod)
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; img-src 'self'; frame-ancestors 'none';"
            )
        else:
            # Relaxed CSP in dev so /docs (Swagger UI) still works
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
                "img-src 'self' data:; "
                "frame-ancestors 'none';"
            )

        return response
