from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.metrics import increment_metric


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        """
        Middleware to log and increment metrics based on response status.

        :param request: The incoming HTTP request.
        :type request: Request
        :param call_next: A callable that processes the request and returns a response.
        :type call_next: Callable[[Request], Response]
        :return: The processed HTTP response.
        :rtype: Response
        """
        response = await call_next(request)
        increment_metric(response.status_code)
        return response
