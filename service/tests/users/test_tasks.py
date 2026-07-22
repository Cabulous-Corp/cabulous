"""Tests for users tasks."""

from unittest.mock import MagicMock, patch

from users.tasks import cleanup_magic_links


@patch("users.tasks.UserMagicLinkToken")
def test_cleanup_magic_links_deletes_expired_and_used(mock_model: MagicMock) -> None:
    mock_qs = MagicMock()
    mock_qs.delete.return_value = (3, None)
    mock_model.objects.filter.return_value = mock_qs

    result = cleanup_magic_links()

    mock_model.objects.filter.assert_called_once()
    assert result == "3 magic links deleted"
