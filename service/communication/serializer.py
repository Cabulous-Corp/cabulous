from __future__ import annotations

import re
from typing import Any, cast

from rest_framework import serializers

SUPPORTED_EVENTS = ("issues", "pull_request", "projects_v2_item")


def extract_issue_references(text: str | None) -> list[int]:
    """
    Extrai referências tipo:
    Fixes #48
    Closes #12
    """
    if not text:
        return []
    return [int(n) for n in re.findall(r"#(\d+)", text)]


class GithubUserSerializer(serializers.Serializer):
    login = serializers.CharField()


class GithubLabelSerializer(serializers.Serializer):
    name = serializers.CharField()


class GithubIssueSerializer(serializers.Serializer):
    number = serializers.IntegerField()
    title = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    assignees = GithubUserSerializer(many=True, required=False, default=list)
    labels = GithubLabelSerializer(many=True, required=False, default=list)
    type = serializers.DictField(required=False, allow_null=True)
    parent_issue_url = serializers.URLField(required=False, allow_null=True)
    user = GithubUserSerializer()
    html_url = serializers.URLField(required=False, allow_null=True)

    def to_internal_value(self, data: dict[str, Any]) -> dict[str, Any]:
        ret = super().to_internal_value(data)

        return {
            "numero": ret.get("number"),
            "titulo": ret.get("title"),
            "responsaveis": [u.get("login") for u in ret.get("assignees", [])],
            "labels": [l.get("name") for l in ret.get("labels", [])],
            "tipo": ret.get("type", {}).get("name") if ret.get("type") else None,
            "parent": ret.get("parent_issue_url"),
            "autor": ret.get("user", {}).get("login"),
            "url": ret.get("html_url"),
        }


class GithubPullRequestSerializer(serializers.Serializer):
    number = serializers.IntegerField()
    title = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    user = GithubUserSerializer()
    assignees = GithubUserSerializer(many=True, required=False, default=list)
    merged = serializers.BooleanField(required=False, default=False)
    body = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    head = serializers.DictField()
    base = serializers.DictField()

    def to_internal_value(self, data: dict[str, Any]) -> dict[str, Any]:
        ret = super().to_internal_value(data)

        # Faz a conversão para o formato desejado (mesmo estilo do parser)
        body_text = ret.get("body") or ""
        title_text = ret.get("title") or ""
        full_text = f"{body_text} {title_text}"

        return {
            "numero": ret.get("number"),
            "titulo": ret.get("title"),
            "autor": ret.get("user", {}).get("login"),
            "responsaveis": [u.get("login") for u in ret.get("assignees", [])],
            "merged": ret.get("merged", False),
            "issues_relacionadas": extract_issue_references(full_text),
            "branch": ret.get("head", {}).get("ref"),
            "base": ret.get("base", {}).get("ref"),
        }


class GithubWebhookSerializer(serializers.Serializer):
    """Validate and normalize incoming GitHub webhook data using specific event serializers."""

    event = serializers.ChoiceField(choices=SUPPORTED_EVENTS)
    payload = serializers.JSONField()

    def validate_payload(self, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise serializers.ValidationError("Payload must be a JSON object.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        event = attrs["event"]
        payload = cast(dict[str, Any], attrs["payload"])

        # Enforce a minimal shape per event before parsing.
        if event == "issues":
            if "action" not in payload or "issue" not in payload:
                raise serializers.ValidationError(
                    {"payload": "For issues event, payload must contain 'action' and 'issue'."}
                )

            action = payload["action"]
            issue_data = payload["issue"]

            if action in ("assigned", "unassigned"):
                assignee_login = payload.get("assignee", {}).get("login")

                # Aproveitamos o serializer de Issue para reaproveitar extração de campos extras
                issue_serializer = GithubIssueSerializer(data=issue_data)
                issue_serializer.is_valid(raise_exception=True)
                parsed_issue = cast(dict[str, Any], issue_serializer.validated_data)

                attrs["normalized"] = {
                    "evento": f"issue_{action}",
                    "issue": parsed_issue.get("numero"),
                    "responsavel": assignee_login,
                    "titulo": parsed_issue.get("titulo"),
                    "url": parsed_issue.get("url"),
                    "labels": parsed_issue.get("labels", []),
                    "tipo": parsed_issue.get("tipo"),
                    "parent": parsed_issue.get("parent"),
                }
            elif action == "closed":
                issue_serializer = GithubIssueSerializer(data=issue_data)
                issue_serializer.is_valid(raise_exception=True)
                parsed_issue = cast(dict[str, Any], issue_serializer.validated_data)

                attrs["normalized"] = {
                    "evento": "issue_closed",
                    "issue": parsed_issue.get("numero"),
                    "titulo": parsed_issue.get("titulo"),
                    "url": parsed_issue.get("url"),
                    "labels": parsed_issue.get("labels", []),
                    "tipo": parsed_issue.get("tipo"),
                    "parent": parsed_issue.get("parent"),
                }
            elif action in ("opened", "edited"):
                issue_serializer = GithubIssueSerializer(data=issue_data)
                issue_serializer.is_valid(raise_exception=True)
                parsed_issue = cast(dict[str, Any], issue_serializer.validated_data)

                attrs["normalized"] = {
                    "evento": f"issue_{'created' if action == 'opened' else 'updated'}",
                    "issue": parsed_issue.get("numero"),
                    "titulo": parsed_issue.get("titulo"),
                    "url": parsed_issue.get("url"),
                    "labels": parsed_issue.get("labels", []),
                    "tipo": parsed_issue.get("tipo"),
                    "parent": parsed_issue.get("parent"),
                    # Aqui incluímos os responsáveis já que criadas e atualizadas podem tê-los
                    "responsaveis": parsed_issue.get("responsaveis", []),
                }
            else:
                attrs["normalized"] = {"evento": "ignored"}

        elif event == "pull_request":
            if "action" not in payload or "pull_request" not in payload:
                raise serializers.ValidationError(
                    {
                        "payload": "For pull_request event, payload must contain 'action' and 'pull_request'."
                    }
                )

            action = payload["action"]
            pr_data = payload["pull_request"]

            if action in ("assigned", "unassigned"):
                assignee_login = payload.get("assignee", {}).get("login")
                attrs["normalized"] = {
                    "evento": f"pr_{action}",
                    "pr": pr_data.get("number"),
                    "responsavel": assignee_login,
                }
            elif action in ("opened", "edited", "closed"):
                pr_serializer = GithubPullRequestSerializer(data=pr_data)
                pr_serializer.is_valid(raise_exception=True)
                parsed_pr = cast(dict[str, Any], pr_serializer.validated_data)

                parsed_pr["url"] = pr_data.get("html_url")

                if action == "closed":
                    event_name = "pr_merged" if parsed_pr.get("merged") else "pr_closed"
                    attrs["normalized"] = {"evento": event_name, "data": parsed_pr}
                else:
                    event_name = "pr_created" if action == "opened" else "pr_updated"
                    attrs["normalized"] = {"evento": event_name, "data": parsed_pr}
            else:
                attrs["normalized"] = {"evento": "ignored"}

        elif event == "projects_v2_item":
            if "action" not in payload or "projects_v2_item" not in payload:
                raise serializers.ValidationError(
                    {
                        "payload": "For projects_v2_item event, payload must contain 'action' and 'projects_v2_item'."
                    }
                )

            action = payload["action"]
            item_data = payload["projects_v2_item"]

            if action == "edited" and item_data.get("content_type") == "Issue":
                content_node_id = item_data.get("content_node_id")

                changes_field = payload.get("changes", {}).get("field_value", {})
                from_status = changes_field.get("from", {}).get("name")
                from_color = changes_field.get("from", {}).get("color")
                to_status = changes_field.get("to", {}).get("name")
                to_color = changes_field.get("to", {}).get("color")

                attrs["normalized"] = {
                    "evento": "project_item_edited",
                    "content_node_id": content_node_id,
                    "from": from_status,
                    "from_color": from_color,
                    "to": to_status,
                    "to_color": to_color,
                }
            else:
                attrs["normalized"] = {"evento": "ignored"}

        normalized = attrs.get("normalized", {})
        if normalized and normalized.get("evento") != "ignored":
            sender_info = payload.get("sender", {})
            normalized["sender"] = sender_info.get("login")
            normalized["sender_avatar"] = sender_info.get("avatar_url")

        return attrs

    def save(self, **kwargs: Any) -> dict[str, Any]:
        validated_data = cast(dict[str, Any], self.validated_data)
        return cast(dict[str, Any], validated_data["normalized"])
