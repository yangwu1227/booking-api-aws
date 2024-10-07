import os

from fastapi import FastAPI

from app.api import endpoints, ping, token


def create_app() -> FastAPI:
    """
    Create an instance of the FastAPI application.
    """
    application = FastAPI(
        title="booking-service",
        docs_url=os.getenv("DOCS_URL") if os.getenv("DOCS_URL") else None,
        redoc_url=None,
    )
    application.include_router(ping.router)
    application.include_router(token.router)
    application.include_router(endpoints.router, prefix="/booking", tags=["booking"])
    return application


app = create_app()
