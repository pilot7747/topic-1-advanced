metrics = {
    "200x": 0,
    "400x": 0,
    "500x": 0,
    "total_requests": 0,
    "tokens_in": 0,
    "tokens_out": 0,
}


def increment_metric(status_code: int) -> None:
    """
    Increments the count of HTTP response status codes for metrics tracking.

    :param status_code: An HTTP status code to categorize and count.
    :type status_code: int
    :return: None
    :rtype: None
    """
    if 200 <= status_code < 300:
        metrics["200x"] += 1
    elif 400 <= status_code < 500:
        metrics["400x"] += 1
    elif status_code >= 500:
        metrics["500x"] += 1
    metrics["total_requests"] += 1


def update_tokens_in(tokens: int) -> None:
    """
    Update the count of tokens received.

    :param tokens: The number of tokens to add to the current count.
    :type tokens: int
    :return: None
    :rtype: None
    """
    metrics["tokens_in"] += tokens


def update_tokens_out(tokens: int) -> None:
    """
    Updates the count of 'tokens_out' in the metrics dictionary by adding the provided number of tokens.

    :param tokens: int
    :return: None
    """
    metrics["tokens_out"] += tokens


def get_metrics() -> dict[str, int]:
    """
    Retrieves a dictionary of metrics with string keys and integer values.

    :return: A dictionary where keys are metric names and values are their corresponding counts.
    :rtype: dict
    """
    return metrics
