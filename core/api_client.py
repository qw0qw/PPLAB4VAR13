"""HTTP-клиент внешнего API фактов."""

import logging
import time
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from typing import Any

import requests

from config.settings import (
    API_CONNECT_TIMEOUT,
    API_MAX_RETRIES,
    API_MAX_RETRY_AFTER,
    API_READ_TIMEOUT,
    CATEGORIES,
)
from config.urls import FACT_API_BASE_URL
from exceptions import FactAPIError

logger = logging.getLogger(__name__)
SESSION = requests.Session()
RETRYABLE_STATUSES = {500, 502, 503, 504}


def _retry_after_seconds(value: str | None) -> float | None:
    """Преобразует заголовок Retry-After в число секунд."""
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value)
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=timezone.utc)
            return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError, OverflowError):
            return None


def fetch_fact(category: str) -> dict[str, Any]:
    """Получает JSON-ответ API для указанной категории."""
    if category not in CATEGORIES:
        raise ValueError(f"Unknown fact category: {category}")

    url = f"{FACT_API_BASE_URL}/random/{category}?json"
    timeout = (API_CONNECT_TIMEOUT, API_READ_TIMEOUT)
    retries = 0
    rate_limit_retried = False

    while True:
        started = time.monotonic()
        try:
            logger.info("API request attempt %s for category %s", retries + 1, category)
            response = SESSION.get(url, timeout=timeout)
            status = response.status_code
            duration = time.monotonic() - started
            logger.info(
                "API response status=%s duration=%.3fs category=%s",
                status,
                duration,
                category,
            )

            if status == 429:
                delay = _retry_after_seconds(response.headers.get("Retry-After"))
                if rate_limit_retried or delay is None or delay > API_MAX_RETRY_AFTER:
                    raise FactAPIError(
                        "API rate limit exceeded.", status_code=status
                    )
                rate_limit_retried = True
                logger.warning("API rate limited; retrying after %.2f seconds", delay)
                time.sleep(delay)
                continue

            if status in RETRYABLE_STATUSES and retries < API_MAX_RETRIES:
                delay = 0.5 * (2 ** retries)
                retries += 1
                logger.warning(
                    "Retrying API request after HTTP %s in %.2f seconds",
                    status,
                    delay,
                )
                time.sleep(delay)
                continue

            if status >= 400:
                raise FactAPIError(
                    f"API returned HTTP {status}.", status_code=status
                )

            try:
                payload = response.json()
            except ValueError as exc:
                raise FactAPIError(
                    "API returned invalid JSON.", status_code=status
                ) from exc

            if not isinstance(payload, dict):
                raise FactAPIError(
                    "API response is not a JSON object.", status_code=status
                )
            return payload

        except (requests.ConnectionError, requests.Timeout) as exc:
            duration = time.monotonic() - started
            if retries < API_MAX_RETRIES:
                delay = 0.5 * (2 ** retries)
                retries += 1
                logger.warning(
                    "API network error after %.3fs; retry %s in %.2fs: %s",
                    duration,
                    retries,
                    delay,
                    exc,
                )
                time.sleep(delay)
                continue
            logger.error("API request failed after retries: %s", exc)
            raise FactAPIError("API connection failed.") from exc
        except FactAPIError as exc:
            logger.error("API request failed: %s", exc)
            raise
        except requests.RequestException as exc:
            logger.error("Unexpected HTTP error: %s", exc)
            raise FactAPIError("API request failed.") from exc
