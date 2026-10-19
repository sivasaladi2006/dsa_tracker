import logging

import pymysql
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("dsa_tracker")


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(pymysql.err.OperationalError)
    @app.exception_handler(pymysql.err.InterfaceError)
    async def database_unavailable(request: Request, exc: Exception):
        # Connection refused, bad credentials, dropped connection.
        logger.error("Database unavailable on %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse(
            status_code=503,
            content={"detail": "Database unavailable"},
            headers={"Retry-After": "5"},
        )

    @app.exception_handler(pymysql.MySQLError)
    async def database_error(request: Request, exc: Exception):
        logger.error("Database error on %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse(status_code=500, content={"detail": "Database error"})

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.error("Unhandled error on %s %s", request.method, request.url.path, exc_info=exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
