from __future__ import annotations

import re
from typing import Any, cast

from rest_framework import serializers

SUPPORTED_EVENTS = ("issues", "pull_request", "projects_v2_item")


def extract_issue_references(text: str | None) -> list[int]:
    """
    Extract issue references such as:
    - Fixes #48
    - Closes #12
    """
    if not text:
        return []
    return [int(number) for number in re.findall(r"#(\d+)", text)]


class GithubIssueSerializer(serializers.Serializer):
    number = serializers.IntegerField()
    title = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    assignees = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    labels = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    type = serializers.DictField(required=False, allow_null=True)
    parent_issue_url = serializers.URLField(required=False, allow_null=True)
    user = serializers.DictField()
    html_url = serializers.URLField(required=False, allow_null=True)

    def to_internal_value(self, data: dict[str, Any]) -> dict[str, Any]:
        parsed = super().to_internal_value(data)
        return {
            "number": parsed.get("number"),
            "title": parsed.get("title"),
            "assignees": [user.get("login") for user in parsed.get("assignees", [])],
            "labels": [label.get("name") for label in parsed.get("labels", [])],
            "issue_type": parsed.get("type", {}).get("name") if parsed.get("type") else None,
            "parent_issue_url": parsed.get("parent_issue_url"),
            "author": parsed.get("user", {}).get("login"),
            "url": parsed.get("html_url"),
        }


class GithubPullRequestSerializer(serializers.Serializer):
    number = serializers.IntegerField()
    title = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    user = serializers.DictField()
    assignees = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    merged = serializers.BooleanField(required=False, default=False)
    body = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    head = serializers.DictField()
    base = serializers.DictField()

    def to_internal_value(self, data: dict[str, Any]) -> dict[str, Any]:
        parsed = super().to_internal_value(data)

        body_text = parsed.get("body") or ""
        title_text = parsed.get("title") or ""
        full_text = f"{body_text} {title_text}"

        return {
            "number": parsed.get("number"),
            "title": parsed.get("title"),
            "author": parsed.get("user", {}).get("login"),
            "assignees": [user.get("login") for user in parsed.get("assignees", [])],
            "merged": parsed.get("merged", False),
            "related_issues": extract_issue_references(full_text),
            "branch": parsed.get("head", {}).get("ref"),
            "base": parsed.get("base", {}).get("ref"),
        }


def _build_issues(payload: dict[str, Any]) -> dict[str, Any]:
    if "action" not in payload or "issue" not in payload:
        raise serializers.ValidationError(
            {"payload": "For issues event, payload must contain 'action' and 'issue'."}
        )

    action = payload["action"]
    if action not in {"assigned", "unassigned", "closed", "opened", "edited"}:
        return {"event_name": "ignored"}

    parser = GithubIssueSerializer(data=payload["issue"])
    parser.is_valid(raise_exception=True)
    parsed = cast(dict[str, Any], parser.validated_data)

    base = {
        "issue_number": parsed.get("number"),
        "title": parsed.get("title"),
        "url": parsed.get("url"),
        "labels": parsed.get("labels", []),
        "issue_type": parsed.get("issue_type"),
        "parent_issue_url": parsed.get("parent_issue_url"),
    }

    if action in {"assigned", "unassigned"}:
        return {
            "event_name": f"issue_{action}",
            "assignee": payload.get("assignee", {}).get("login"),
            **base,
        }
    if action == "closed":
        return {"event_name": "issue_closed", **base}
    return {
        "event_name": f"issue_{'created' if action == 'opened' else 'updated'}",
        "assignees": parsed.get("assignees", []),
        **base,
    }


def _build_pull_request(payload: dict[str, Any]) -> dict[str, Any]:
    if "action" not in payload or "pull_request" not in payload:
        raise serializers.ValidationError(
            {
                "payload": (
                    "For pull_request event, payload must contain 'action' and 'pull_request'."
                )
            }
        )

    action = payload["action"]
    if action not in {"assigned", "unassigned", "opened", "edited", "closed"}:
        return {"event_name": "ignored"}

    pr_data = payload["pull_request"]
    if action in {"assigned", "unassigned"}:
        return {
            "event_name": f"pr_{action}",
            "pr_number": pr_data.get("number"),
            "assignee": payload.get("assignee", {}).get("login"),
        }

    parser = GithubPullRequestSerializer(data=pr_data)
    parser.is_valid(raise_exception=True)
    parsed = cast(dict[str, Any], parser.validated_data)
    parsed["url"] = pr_data.get("html_url")

    if action == "closed":
        event_name = "pr_merged" if parsed.get("merged") else "pr_closed"
    else:
        event_name = "pr_created" if action == "opened" else "pr_updated"

    return {"event_name": event_name, "pull_request": parsed}


def _build_projects_v2_item(payload: dict[str, Any]) -> dict[str, Any]:
    if "action" not in payload or "projects_v2_item" not in payload:
        raise serializers.ValidationError(
            {
                "payload": (
                    "For projects_v2_item event, payload must contain "
                    "'action' and 'projects_v2_item'."
                )
            }
        )

    action = payload["action"]
    item = payload["projects_v2_item"]
    if action != "edited" or item.get("content_type") != "Issue":
        return {"event_name": "ignored"}

    changes = payload.get("changes", {}).get("field_value", {})
    return {
        "event_name": "project_item_edited",
        "content_node_id": item.get("content_node_id"),
        "from_status": changes.get("from", {}).get("name"),
        "from_color": changes.get("from", {}).get("color"),
        "to_status": changes.get("to", {}).get("name"),
        "to_color": changes.get("to", {}).get("color"),
    }


ACTION_BUILDERS = {
    "issues": _build_issues,
    "pull_request": _build_pull_request,
    "projects_v2_item": _build_projects_v2_item,
}


class GithubWebhookSerializer(serializers.Serializer):
    """Validate and normalize incoming GitHub webhook payloads."""

    event = serializers.ChoiceField(choices=SUPPORTED_EVENTS)
    payload = serializers.JSONField()

    def validate_payload(self, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise serializers.ValidationError("Payload must be a JSON object.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        event = attrs["event"]
        payload = cast(dict[str, Any], attrs["payload"])

        builder = ACTION_BUILDERS.get(event)
        if builder is not None:
            attrs["normalized"] = builder(payload)

        normalized = attrs.get("normalized", {})
        if normalized and normalized.get("event_name") != "ignored":
            sender_info = payload.get("sender", {})
            normalized["sender"] = sender_info.get("login")
            normalized["sender_avatar_url"] = sender_info.get("avatar_url")

        return attrs

    def save(self, **kwargs: Any) -> dict[str, Any]:
        validated_data = cast(dict[str, Any], self.validated_data)
        return cast(dict[str, Any], validated_data["normalized"])
