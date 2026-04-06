import datetime
import os
from typing import Any

import requests

from communication.models.discord_message import DiscordEmbed, DiscordEmbedAuthor, DiscordEmbedField
from communication.services import DiscordService


def _is_http_url_candidate(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def build_discord_embed(data: dict[str, Any]) -> DiscordEmbed | None:
    """Build a Discord embed based on normalized GitHub webhook data."""
    event_name = data.get("event_name")

    if not event_name or event_name == "ignored":
        return None

    sender = data.get("sender", "User")
    sender_avatar_url = data.get("sender_avatar_url", "")

    timestamp_iso = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    author = (
        DiscordEmbedAuthor(name=sender, icon_url=sender_avatar_url)
        if sender_avatar_url and _is_http_url_candidate(sender_avatar_url)
        else DiscordEmbedAuthor(name=sender)
    )

    if event_name.startswith("issue_"):
        issue_number = data.get("issue_number")
        title = data.get("title")
        url = data.get("url")

        if event_name == "issue_created":
            return DiscordEmbed(
                title=f"🆕 New Issue: #{issue_number}",
                description=f"[{title}]({url})",
                color=5763719,
                author=author,
                timestamp=timestamp_iso,
            )
        if event_name == "issue_updated":
            return DiscordEmbed(
                title=f"✏️ Issue #{issue_number} Updated",
                description=f"[{title}]({url})",
                color=16776960,
                author=author,
                timestamp=timestamp_iso,
            )
        if event_name == "issue_closed":
            return DiscordEmbed(
                title=f"✅ Issue #{issue_number} Closed",
                description=f"[{title}]({url})",
                color=15548997,
                author=author,
                timestamp=timestamp_iso,
            )
        if event_name == "issue_assigned":
            assignee = data.get("assignee")
            return DiscordEmbed(
                title=f"👤 Issue #{issue_number} Assigned to {assignee}",
                description=f"Open issue: [{title}]({url})",
                color=3447003,
                author=author,
                timestamp=timestamp_iso,
            )
        if event_name == "issue_unassigned":
            assignee = data.get("assignee")
            return DiscordEmbed(
                title=f"➖ Issue #{issue_number} Unassigned from {assignee}",
                description=f"Open issue: [{title}]({url})",
                color=9807270,
                author=author,
                timestamp=timestamp_iso,
            )

    if event_name.startswith("pr_"):
        pull_request = data.get("pull_request", {})
        pr_number = pull_request.get("number") or data.get("pr_number")
        title = pull_request.get("title", "")
        url = pull_request.get("url", "")
        linked_title = f"[{title}]({url})" if url else title

        if event_name == "pr_created":
            return DiscordEmbed(
                title=f"🔄 New Pull Request: #{pr_number}",
                description=linked_title,
                color=5763719,
                author=author,
                timestamp=timestamp_iso,
            )
        if event_name == "pr_merged":
            return DiscordEmbed(
                title=f"🎉 Pull Request Merged: #{pr_number}",
                description=linked_title,
                color=10181046,
                author=author,
                timestamp=timestamp_iso,
            )
        if event_name == "pr_closed":
            return DiscordEmbed(
                title=f"❌ Pull Request Closed: #{pr_number}",
                description=linked_title,
                color=15548997,
                author=author,
                timestamp=timestamp_iso,
            )
        if event_name == "pr_assigned":
            assignee = data.get("assignee")
            return DiscordEmbed(
                title=f"👤 Pull Request Assigned: #{pr_number}",
                description=f"**{assignee}** was assigned to PR {linked_title}",
                color=3447003,
                author=author,
                timestamp=timestamp_iso,
            )
        if event_name == "pr_unassigned":
            assignee = data.get("assignee")
            return DiscordEmbed(
                title=f"➖ Pull Request Unassigned: #{pr_number}",
                description=f"**{assignee}** was unassigned from PR {linked_title}",
                color=9807270,
                author=author,
                timestamp=timestamp_iso,
            )

    if event_name == "project_item_edited":
        node_id = data.get("content_node_id")

        github_token = os.getenv("GITHUB__ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN") or ""
        issue_title = fetch_github_node_title(node_id, github_token)
        from_status = data.get("from_status")
        to_status = data.get("to_status")
        from_color = data.get("from_color", "")
        to_color = data.get("to_color", "")
        centered_arrow = "         v"

        if from_status is None and to_status is None:
            return None

        color_emojis = {
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

        color_ansi = {
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

        from_color_tag = color_emojis.get(from_color.upper(), "") if from_color else ""
        to_color_tag = color_emojis.get(to_color.upper(), "") if to_color else ""

        from_ansi = color_ansi.get(from_color.upper(), "0") if from_color else "0"
        to_ansi = color_ansi.get(to_color.upper(), "0") if to_color else "0"

        from_text = f"```ansi\n\u001b[0;{from_ansi}m{from_color_tag} {from_status}\u001b[0m\n```"
        to_text = f"```ansi\n\u001b[0;{to_ansi}m{to_color_tag} {to_status}\u001b[0m\n```"

        return DiscordEmbed(
            title=f"Issue: {issue_title}",
            description="🔄 Status changed",
            color=5814783,
            author=author,
            timestamp=timestamp_iso,
            fields=[
                DiscordEmbedField(
                    name="Transition",
                    value=f"{from_text}{centered_arrow}\n{to_text}",
                ),
            ],
        )

    return DiscordEmbed(
        title="ℹ️ New Event",
        description=f"`{event_name}` was triggered.",
        color=9807270,
        author=author,
        timestamp=timestamp_iso,
    )


def post_to_discord(webhook_url: str, validated_data: dict[str, Any]) -> bool:
    embed = build_discord_embed(validated_data)

    if embed is None:
        return False

    try:
        DiscordService.send_channel_embed(
            webhook_url=webhook_url,
            embeds=[embed],
        )
        return True
    except Exception as exc:
        print(f"Error sending message to Discord: {exc}")
        return False


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
