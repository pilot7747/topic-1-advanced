from typing import Callable

from app.core.metrics import increment_metric
from app.core.security import check_token
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Class to handle authentication for incoming requests, extending BaseHTTPMiddleware.

    Methods
    -------
    dispatch(request: Request, call_next: Callable[[Request], Response]) -> Response
        Intercepts incoming requests, checks authorization, and invokes the next middleware or endpoint.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        """
        Dispatches the incoming request after performing necessary checks and normalizations.

        :param request: The incoming HTTP request.
        :type request: Request
        :param call_next: A callable that processes the next request in the chain.
        :type call_next: Callable[[Request], Response]
        :return: The response after processing the request.
        :rtype: Response
        """
        normalized_path = request.url.path.rstrip("/")
        if normalized_path in ["/docs", "/openapi.json", "/signup"]:
            return await call_next(request)

        token = request.headers.get("Authorization")
        if not await check_token(token):
            increment_metric(403)
            return JSONResponse(status_code=403, content={"detail": "Unauthorized"})

        return await call_next(request)
