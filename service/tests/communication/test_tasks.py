"""Tests for communication tasks."""

from unittest.mock import MagicMock, patch

from communication.tasks import (
    send_discord_channel_embed_by_purpose_task,
    send_discord_channel_embed_task,
    send_discord_channel_message_by_purpose_task,
    send_discord_channel_message_from_template_by_purpose_task,
    send_discord_channel_message_from_template_task,
    send_discord_channel_message_task,
    send_html_template_email_task,
    send_simple_email_task,
)


@patch("communication.tasks.EmailService")
def test_send_simple_email_task(mock_svc: MagicMock) -> None:
    mock_svc.send_simple_email.return_value = 1
    result = send_simple_email_task(
        subject="Hi",
        recipients=["a@b.com"],
        body="hello",
    )
    mock_svc.send_simple_email.assert_called_once_with(
        subject="Hi",
        recipients=["a@b.com"],
        body="hello",
        from_email=None,
        cc=None,
        bcc=None,
        reply_to=None,
        fail_silently=False,
    )
    assert result == 1


@patch("communication.tasks.EmailService")
def test_send_html_template_email_task(mock_svc: MagicMock) -> None:
    mock_svc.send_html_template_email.return_value = 1
    result = send_html_template_email_task(
        subject="Hi",
        recipients=["a@b.com"],
        template_path="email/welcome.html",
        context={"name": "A"},
    )
    mock_svc.send_html_template_email.assert_called_once_with(
        subject="Hi",
        recipients=["a@b.com"],
        template_path="email/welcome.html",
        context={"name": "A"},
        text_body=None,
        from_email=None,
        cc=None,
        bcc=None,
        reply_to=None,
        fail_silently=False,
    )
    assert result == 1


@patch("communication.tasks.DiscordService")
def test_send_discord_channel_message_task(mock_svc: MagicMock) -> None:
    send_discord_channel_message_task(
        webhook_url="https://hooks.test",
        content="hi",
    )
    mock_svc.send_channel_message.assert_called_once_with(
        webhook_url="https://hooks.test",
        content="hi",
    )


@patch("communication.tasks.DiscordService")
def test_send_discord_channel_message_by_purpose_task(mock_svc: MagicMock) -> None:
    send_discord_channel_message_by_purpose_task(
        purpose="alerts",
        content="hello",
    )
    mock_svc.send_channel_message_by_purpose.assert_called_once_with(
        purpose="alerts",
        content="hello",
    )


@patch("communication.tasks.DiscordService")
def test_send_discord_channel_message_from_template_task(mock_svc: MagicMock) -> None:
    send_discord_channel_message_from_template_task(
        webhook_url="https://hooks.test",
        template_path="discord/alert.html",
        context={"env": "prod"},
    )
    mock_svc.send_channel_message_from_template.assert_called_once_with(
        webhook_url="https://hooks.test",
        template_path="discord/alert.html",
        context={"env": "prod"},
    )


@patch("communication.tasks.DiscordService")
def test_send_discord_channel_message_from_template_by_purpose_task(mock_svc: MagicMock) -> None:
    send_discord_channel_message_from_template_by_purpose_task(
        purpose="alerts",
        template_path="discord/alert.html",
        context={"env": "prod"},
    )
    mock_svc.send_channel_message_from_template_by_purpose.assert_called_once_with(
        purpose="alerts",
        template_path="discord/alert.html",
        context={"env": "prod"},
    )


@patch("communication.tasks.DiscordService")
def test_send_discord_channel_embed_task(mock_svc: MagicMock) -> None:
    send_discord_channel_embed_task(
        webhook_url="https://hooks.test",
        content="hi",
        embeds=[{"title": "Test"}],
    )
    mock_svc.send_channel_embed.assert_called_once()
    call_kwargs = mock_svc.send_channel_embed.call_args[1]
    assert call_kwargs["webhook_url"] == "https://hooks.test"
    assert call_kwargs["content"] == "hi"
    assert len(call_kwargs["embeds"]) == 1


@patch("communication.tasks.DiscordService")
def test_send_discord_channel_embed_by_purpose_task(mock_svc: MagicMock) -> None:
    send_discord_channel_embed_by_purpose_task(
        purpose="alerts",
        content="hi",
        embeds=None,
    )
    mock_svc.send_channel_embed_by_purpose.assert_called_once_with(
        purpose="alerts",
        content="hi",
        embeds=None,
    )
