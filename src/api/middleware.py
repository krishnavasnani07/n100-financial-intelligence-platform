import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.logger import get_logger

logger = get_logger("api_request_logger")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()

        response = await call_next(request)

        process_time = (time.perf_counter() - start_time) * 1000

        # Log basic HTTP request/response details: METHOD path status_code duration
        logger.info(
            f"API {request.method} {request.url.path} {response.status_code} {process_time:.2f}ms"
        )
        return response
