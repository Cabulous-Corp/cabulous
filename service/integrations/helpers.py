import datetime
import os
from collections.abc import Callable
from typing import Any

import requests

from communication.models.discord_message import DiscordEmbed, DiscordEmbedAuthor, DiscordEmbedField

_COLOR_EMOJIS = {
    "RED": "🔴",
    "BLUE": "🔵",
    "GREEN": "🟢",
    "YELLOW": "🟡",
    "PURPLE": "🟣",
    "ORANGE": "🟠",
    "BROWN": "🟤",
    "PINK": "🌸",
    "GRAY": "⚪",
    "BLACK": "⚫",
    "WHITE": "⚪",
    "MINT": "🍃",
}

_COLOR_ANSI = {
    "RED": "31",
    "BLUE": "34",
    "GREEN": "32",
    "YELLOW": "33",
    "PURPLE": "35",
    "ORANGE": "33",
    "BROWN": "30",
    "PINK": "35",
    "GRAY": "30",
    "BLACK": "30",
    "WHITE": "37",
    "MINT": "32",
}


def _issue_ctx(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "issue_number": data.get("issue_number"),
        "title": data.get("title"),
        "url": data.get("url"),
    }


def _issue_assigned_ctx(data: dict[str, Any]) -> dict[str, Any]:
    return {**_issue_ctx(data), "assignee": data.get("assignee")}


def _pr_ctx(data: dict[str, Any]) -> dict[str, Any]:
    pr = data.get("pull_request", {})
    number = pr.get("number") or data.get("pr_number")
    title = pr.get("title", "")
    url = pr.get("url", "")
    return {"pr_number": number, "linked_title": f"[{title}]({url})" if url else title}


def _pr_assigned_ctx(data: dict[str, Any]) -> dict[str, Any]:
    return {**_pr_ctx(data), "assignee": data.get("assignee")}


# ponytail: per-event formatter table replaces the per-event if/return switch.
EVENT_FORMATTERS: dict[str, tuple[str, str, int, Callable[[dict[str, Any]], dict[str, Any]]]] = {
    "issue_created": (
        "🆕 New Issue: #{issue_number}",
        "[{title}]({url})",
        5763719,
        _issue_ctx,
    ),
    "issue_updated": (
        "✏️ Issue #{issue_number} Updated",
        "[{title}]({url})",
        16776960,
        _issue_ctx,
    ),
    "issue_closed": (
        "✅ Issue #{issue_number} Closed",
        "[{title}]({url})",
        15548997,
        _issue_ctx,
    ),
    "issue_assigned": (
        "👤 Issue #{issue_number} Assigned to {assignee}",
        "Open issue: [{title}]({url})",
        3447003,
        _issue_assigned_ctx,
    ),
    "issue_unassigned": (
        "➖ Issue #{issue_number} Unassigned from {assignee}",
        "Open issue: [{title}]({url})",
        9807270,
        _issue_assigned_ctx,
    ),
    "pr_created": (
        "🔄 New Pull Request: #{pr_number}",
        "{linked_title}",
        5763719,
        _pr_ctx,
    ),
    "pr_merged": (
        "🎉 Pull Request Merged: #{pr_number}",
        "{linked_title}",
        10181046,
        _pr_ctx,
    ),
    "pr_closed": (
        "❌ Pull Request Closed: #{pr_number}",
        "{linked_title}",
        15548997,
        _pr_ctx,
    ),
    "pr_assigned": (
        "👤 Pull Request Assigned: #{pr_number}",
        "**{assignee}** was assigned to PR {linked_title}",
        3447003,
        _pr_assigned_ctx,
    ),
    "pr_unassigned": (
        "➖ Pull Request Unassigned: #{pr_number}",
        "**{assignee}** was unassigned from PR {linked_title}",
        9807270,
        _pr_assigned_ctx,
    ),
}


def _colored_block(status: str | None, color: str) -> str:
    upper = color.upper() if color else ""
    emoji = _COLOR_EMOJIS.get(upper, "") if color else ""
    ansi = _COLOR_ANSI.get(upper, "0") if color else "0"
    return f"```ansi\n\u001b[0;{ansi}m{emoji} {status}\u001b[0m\n```"


def _project_item_embed(
    data: dict[str, Any], author: DiscordEmbedAuthor, ts: str
) -> DiscordEmbed | None:
    from_status = data.get("from_status")
    to_status = data.get("to_status")
    if from_status is None and to_status is None:
        return None

    node_id = data.get("content_node_id")
    token = os.getenv("GITHUB__ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN") or ""
    issue_title = fetch_github_node_title(node_id, token)

    from_block = _colored_block(from_status, data.get("from_color", ""))
    to_block = _colored_block(to_status, data.get("to_color", ""))
    cursor = "         v"

    return DiscordEmbed(
        title=f"Issue: {issue_title}",
        description="🔄 Status changed",
        color=5814783,
        author=author,
        timestamp=ts,
        fields=[
            DiscordEmbedField(
                name="Transition",
                value=f"{from_block}{cursor}\n{to_block}",
            ),
        ],
    )


def build_discord_embed(data: dict[str, Any]) -> DiscordEmbed | None:
    """Build a Discord embed based on normalized GitHub webhook data."""
    event_name = data.get("event_name")
    if not event_name or event_name == "ignored":
        return None

    sender = data.get("sender", "User")
    avatar = data.get("sender_avatar_url", "")
    timestamp_iso = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    author = (
        DiscordEmbedAuthor(name=sender, icon_url=avatar)
        if avatar and avatar.startswith(("http://", "https://"))
        else DiscordEmbedAuthor(name=sender)
    )

    if event_name == "project_item_edited":
        return _project_item_embed(data, author, timestamp_iso)

    fmt = EVENT_FORMATTERS.get(event_name)
    if fmt is not None:
        title_tpl, desc_tpl, color, ctx_fn = fmt
        ctx = ctx_fn(data)
        return DiscordEmbed(
            title=title_tpl.format(**ctx),
            description=desc_tpl.format(**ctx),
            color=color,
            author=author,
            timestamp=timestamp_iso,
        )

    return DiscordEmbed(
        title="ℹ️ New Event",
        description=f"`{event_name}` was triggered.",
        color=9807270,
        author=author,
        timestamp=timestamp_iso,
    )


def fetch_github_node_title(node_id: str | None, github_token: str) -> str:
    if not node_id:
        return "Untitled"

    if not github_token:
        print("Missing GitHub token for GraphQL lookup (GITHUB__ACCESS_TOKEN).")
        return f"Item {str(node_id)[:8]}"

    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"Bearer {github_token}"}

    query = """
    query($id: ID!) {
      node(id: $id) {
        __typename
        ... on Issue { title }
        ... on PullRequest { title }
        ... on DraftIssue { title }
        ... on ProjectV2Item {
          content {
            __typename
            ... on Issue { title }
            ... on PullRequest { title }
            ... on DraftIssue { title }
          }
        }
      }
    }
    """

    try:
        response = requests.post(
            url,
            json={"query": query, "variables": {"id": node_id}},
            headers=headers,
            timeout=5,
        )
        if response.ok:
            response_data = response.json()
            node = response_data.get("data", {}).get("node")
            if node:
                direct_title = node.get("title")
                if direct_title:
                    return direct_title

                content = node.get("content") or {}
                content_title = content.get("title")
                if content_title:
                    return content_title

            errors = response_data.get("errors")
            if errors:
                print(f"GitHub GraphQL error: {errors}")
    except Exception as exc:
        print(f"Error while fetching title from GitHub: {exc}")

    return f"Item {str(node_id)[:8]}"
