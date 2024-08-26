from app.core.metrics import metrics
from app.core.security import verify_token
from fastapi import APIRouter, Depends

router = APIRouter()


@router.get("/metrics/", dependencies=[Depends(verify_token)])
async def get_metrics() -> dict[str, int]:
    """
    Fetches and returns application metrics.

    :return: A dictionary containing application metrics with metric names as keys and values as integers.
    :rtype: dict[str, int]
    """
    return metrics
