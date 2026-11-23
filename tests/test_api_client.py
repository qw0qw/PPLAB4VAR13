"""Тесты HTTP-клиента API."""

from unittest.mock import Mock

import pytest
import requests

from core import api_client
from exceptions import FactAPIError


def test_fetch_fact_returns_dict(monkeypatch: pytest.MonkeyPatch) -> None:
    """Успешный ответ API возвращается как словарь."""
    response = Mock(status_code=200)
    response.json.return_value = {"text": "A test fact"}
    monkeypatch.setattr(api_client.SESSION, "get", Mock(return_value=response))

    assert api_client.fetch_fact("trivia") == {"text": "A test fact"}


def test_fetch_fact_retries_server_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """HTTP 503 повторяется три раза, после чего выбрасывается ошибка."""
    response = Mock(status_code=503, headers={})
    monkeypatch.setattr(api_client.SESSION, "get", Mock(return_value=response))
    monkeypatch.setattr(api_client.time, "sleep", Mock())

    with pytest.raises(FactAPIError) as error:
        api_client.fetch_fact("trivia")

    assert error.value.status_code == 503
    assert api_client.SESSION.get.call_count == 3


def test_fetch_fact_retries_connection_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Сетевые ошибки повторяются до исчерпания лимита."""
    request = Mock(side_effect=requests.ConnectionError("offline"))
    monkeypatch.setattr(api_client.SESSION, "get", request)
    monkeypatch.setattr(api_client.time, "sleep", Mock())

    with pytest.raises(FactAPIError):
        api_client.fetch_fact("trivia")

    assert request.call_count == 3


def test_fetch_fact_succeeds_after_two_server_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """После двух временных HTTP-ошибок клиент принимает успешный ответ."""
    failed_response = Mock(status_code=503, headers={})
    success_response = Mock(status_code=200)
    success_response.json.return_value = {"text": "Recovered fact"}
    request = Mock(
        side_effect=[failed_response, failed_response, success_response]
    )
    monkeypatch.setattr(api_client.SESSION, "get", request)
    monkeypatch.setattr(api_client.time, "sleep", Mock())

    assert api_client.fetch_fact("trivia") == {"text": "Recovered fact"}
    assert request.call_count == 3
