import datetime
import os
from typing import Any

import requests

from communication.models.discord_message import DiscordEmbed, DiscordEmbedAuthor, DiscordEmbedField
from communication.services import DiscordService


def _is_http_url_candidate(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def build_discord_embed(data: dict[str, Any]) -> DiscordEmbed | None:
    """Monta um embed do Discord dependendo do evento."""
    evento = data.get("evento")

    if not evento or evento == "ignored":
        return None

    # Extraímos as informações de autor globais para usar em todos os embeds
    sender = data.get("sender", "Usuário")
    sender_avatar = data.get("sender_avatar", "")

    # Para a data no formato ISO ISO8601 com Z do Discord
    timestamp_iso = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    # Configuração do autor do embed (só adiciona o ícone se ele existir)
    author = (
        DiscordEmbedAuthor(name=sender, icon_url=sender_avatar)
        if sender_avatar and _is_http_url_candidate(sender_avatar)
        else DiscordEmbedAuthor(name=sender)
    )

    if evento.startswith("issue_"):
        issue_num = data.get("issue")
        titulo = data.get("titulo")
        url = data.get("url")

        if evento == "issue_created":
            return DiscordEmbed(
                title=f"🆕 Nova Issue: #{issue_num}",
                description=f"[{titulo}]({url})",
                color=5763719,
                author=author,
                timestamp=timestamp_iso,
            )
        elif evento == "issue_updated":
            return DiscordEmbed(
                title=f"✏️ Issue #{issue_num} Atualizada ",
                description=f"[{titulo}]({url})",
                color=16776960,
                author=author,
                timestamp=timestamp_iso,
            )
        elif evento == "issue_closed":
            return DiscordEmbed(
                title=f"✅ Issue #{issue_num} Fechada",
                description=f"[{titulo}]({url})",
                color=15548997,
                author=author,
                timestamp=timestamp_iso,
            )
        elif evento == "issue_assigned":
            responsavel = data.get("responsavel")
            return DiscordEmbed(
                title=f"👤 Issue #{issue_num} Atribuída a {responsavel}",
                description=f"Acesse a Issue: [{titulo}]({url})",
                color=3447003,
                author=author,
                timestamp=timestamp_iso,
            )
        elif evento == "issue_unassigned":
            responsavel = data.get("responsavel")
            return DiscordEmbed(
                title=f"➖ Issue #{issue_num} Desatribuída de {responsavel}",
                description=f"Acesse a Issue: [{titulo}]({url})",
                color=9807270,
                author=author,
                timestamp=timestamp_iso,
            )

    elif evento.startswith("pr_"):
        pr_data = data.get("data", {})
        pr_num = pr_data.get("numero") or data.get("pr")
        titulo = pr_data.get("titulo", "")
        # Adicionei a tentativa de buscar a URL do PR, caso seu dict suporte
        url = pr_data.get("url", "")
        url_str = f"[{titulo}]({url})" if url else titulo

        if evento == "pr_created":
            return DiscordEmbed(
                title=f"🔄 Novo Pull Request: #{pr_num}",
                description=url_str,
                color=5763719,
                author=author,
                timestamp=timestamp_iso,
            )
        elif evento == "pr_merged":
            return DiscordEmbed(
                title=f"🎉 Pull Request Merged: #{pr_num}",
                description=url_str,
                color=10181046,
                author=author,
                timestamp=timestamp_iso,
            )
        elif evento == "pr_closed":
            return DiscordEmbed(
                title=f"❌ Pull Request Fechado: #{pr_num}",
                description=url_str,
                color=15548997,
                author=author,
                timestamp=timestamp_iso,
            )
        elif evento == "pr_assigned":
            responsavel = data.get("responsavel")
            return DiscordEmbed(
                title=f"👤 PR Atribuído: #{pr_num}",
                description=f"**{responsavel}** foi atribuído ao PR {url_str}",
                color=3447003,
                author=author,
                timestamp=timestamp_iso,
            )

    elif evento == "project_item_edited":
        node_id = data.get("content_node_id")

        github_token = os.getenv("GITHUB__ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN") or ""
        titulo_real = fetch_github_node_title(node_id, github_token)
        from_status = data.get("from")
        to_status = data.get("to")
        from_color = data.get("from_color", "")
        to_color = data.get("to_color", "")
        seta_centralizada = "⠀⠀⠀⠀⠀⠀⠀⠀⠀↓"

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

        from_color_emoji = color_emojis.get(from_color.upper(), "") if from_color else ""
        to_color_emoji = color_emojis.get(to_color.upper(), "") if to_color else ""

        from_ansi = color_ansi.get(from_color.upper(), "0") if from_color else "0"
        to_ansi = color_ansi.get(to_color.upper(), "0") if to_color else "0"

        from_str = f"```ansi\n\u001b[0;{from_ansi}m{from_color_emoji} {from_status}\u001b[0m\n```"
        to_str = f"```ansi\n\u001b[0;{to_ansi}m{to_color_emoji} {to_status}\u001b[0m\n```"

        return DiscordEmbed(
            title=f"Issue: {titulo_real}",
            description="🔄 Status Alterado",
            color=5814783,
            author=author,
            timestamp=timestamp_iso,
            fields=[
                DiscordEmbedField(
                    name="Transicao",
                    value=f"{from_str}{seta_centralizada}\n{to_str}",
                ),
            ],
        )

    return DiscordEmbed(
        title="ℹ️ Novo Evento",
        description=f"`{evento}` disparado.",
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
    except Exception as e:
        print(f"Erro ao enviar para o Discord: {e}")
        return False


def fetch_github_node_title(node_id: str | None, github_token: str) -> str:
    if not node_id:
        return "Sem Título"

    if not github_token:
        print("GitHub token ausente para consulta GraphQL (GITHUB__ACCESS_TOKEN).")
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
            url, json={"query": query, "variables": {"id": node_id}}, headers=headers, timeout=5
        )
        if response.ok:
            data = response.json()
            node = data.get("data", {}).get("node")
            if node:
                direct_title = node.get("title")
                if direct_title:
                    return direct_title

                content = node.get("content") or {}
                content_title = content.get("title")
                if content_title:
                    return content_title

            errors = data.get("errors")
            if errors:
                print(f"Erro GraphQL GitHub: {errors}")
    except Exception as e:
        print(f"Erro ao buscar título no GitHub: {e}")

    return f"Item {str(node_id)[:8]}"
