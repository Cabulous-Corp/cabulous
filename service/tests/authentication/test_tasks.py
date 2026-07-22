"""Tests for authentication tasks."""

from unittest.mock import MagicMock, patch

from authentication.tasks import flush_expired_tokens


@patch("authentication.tasks.call_command")
def test_flush_expired_tokens_calls_command(mock_call_command: MagicMock) -> None:
    result = flush_expired_tokens()
    mock_call_command.assert_called_once_with("flushexpiredtokens")
    assert result == "expired JWT tokens flushed"
