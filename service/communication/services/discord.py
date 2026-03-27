import requests


class DiscordService:
    @staticmethod
    def _send(payload: dict, webhook_url: str = ""):
        try:
            response = requests.post(webhook_url, json=payload, timeout=5)
            if not (200 <= response.status_code < 300):
                raise Exception("Erro ao enviar mensagem")
        except requests.RequestException as e:
            raise Exception(f"Request failed: {e}")

    @staticmethod
    def send_message(webhook_url: str, content: str):
        payload = {"content": content}
        DiscordService._send(payload, webhook_url)

    @staticmethod
    def send_embed(
        webhook_url: str,
        title: str = "",
        description: str = "",
        color: int | None = None,
        url: str = "",
        timestamp: str = "",
        footer: dict | None = None,
        image: dict | None = None,
        thumbnail: dict | None = None,
        author: dict | None = None,
        fields: list[dict] | None = None,
        content: str = "",
    ):
        """Envia uma mensagem em formato embed para um webhook do Discord.

        A função recebe os elementos principais de um embed como parâmetros
        opcionais, monta o payload no formato esperado pela API do Discord
        e envia a requisição.

        Args:
            webhook_url: URL do webhook do Discord.
            title: Título do embed.
            description: Descrição principal do embed.
            color: Cor do embed em decimal (ex.: 5814783).
            url: URL associada ao título do embed.
            timestamp: Data/hora em ISO 8601 (ex.: 2026-03-26T00:00:00Z).
            footer: Rodapé no formato {"text": "...", "icon_url": "..."}.
            image: Imagem principal no formato {"url": "..."}.
            thumbnail: Thumbnail no formato {"url": "..."}.
            author: Autor no formato
                {"name": "...", "url": "...", "icon_url": "..."}.
            fields: Lista de campos no formato
                [{"name": "...", "value": "...", "inline": False}].
            content: Conteúdo textual opcional da mensagem junto do embed.

        Example:
            DiscordService.send_embed(
                webhook_url="https://discord.com/api/webhooks/...",
                title="Boas-vindas",
                description="Chegou membro novo!",
                color=5814783,
                fields=[
                    {"name": "Canal", "value": "#apresentacoes", "inline": True}
                ],
            )
        """
        embed = {}

        if title:
            embed["title"] = title
        if description:
            embed["description"] = description
        if color is not None:
            embed["color"] = color
        if url:
            embed["url"] = url
        if timestamp:
            embed["timestamp"] = timestamp
        if footer:
            embed["footer"] = footer
        if image:
            embed["image"] = image
        if thumbnail:
            embed["thumbnail"] = thumbnail
        if author:
            embed["author"] = author
        if fields:
            embed["fields"] = fields

        payload: dict[str, object] = {"embeds": [embed]}
        if content:
            payload["content"] = content

        DiscordService._send(payload, webhook_url)
