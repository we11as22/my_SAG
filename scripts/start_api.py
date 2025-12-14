"""Start SAG API service

Production environment startup script
"""

import uvicorn

from sag.core.config.settings import get_settings


def main():
    """Start API"""
    settings = get_settings()

    # Get configuration from environment variables, or use defaults
    host = getattr(settings, "api_host", "0.0.0.0")
    port = getattr(settings, "api_port", 8000)
    workers = getattr(settings, "api_workers", 4)
    debug = getattr(settings, "debug", False)

    print(f"🚀 Starting SAG API service")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Workers: {workers if not debug else 1}")
    print(f"   Debug mode: {debug}")

    uvicorn.run(
        "sag.api.main:app",
        host=host,
        port=port,
        workers=workers if not debug else 1,
        reload=debug,
        log_level="info" if not debug else "debug",
    )


if __name__ == "__main__":
    main()

