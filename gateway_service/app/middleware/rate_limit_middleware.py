from typing import Awaitable, Callable

from app.core.config import RATE_LIMIT, RATE_LIMIT_KEY_PREFIX
from app.core.metrics import increment_metric
from app.core.security import ADMIN_TOKEN
from app.db.database import redis
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Handles the dispatch of requests ensuring that rate limiting is respected.
        If the user token in the request headers is absent or matches the ADMIN_TOKEN, the request is passed through.
        Otherwise, the request count is checked against the defined rate limit and increments the count if not exceeded.

        :param request: Incoming HTTP request object
        :type request: Request
        :param call_next: A callable to process the request and return a response
        :type call_next: Callable[[Request], Response]
        :return: The resulting HTTP response after processing
        :rtype: Response
        """
        user_token = request.headers.get("Authorization")
        if not user_token or user_token == ADMIN_TOKEN:
            return await call_next(request)

        if request.url.path.rstrip("/") != "/chat":
            return await call_next(request)

        user_key = f"{RATE_LIMIT_KEY_PREFIX}:{user_token}"
        count = await redis.get(user_key)
        if count and int(count) >= RATE_LIMIT:
            increment_metric(429)
            return JSONResponse(
                status_code=429, content={"detail": "Rate limit exceeded"}
            )

        await redis.incr(user_key)
        await redis.expire(user_key, 60)
        return await call_next(request)
