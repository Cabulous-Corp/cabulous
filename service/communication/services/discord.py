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
    def send_message(content: str, webhook_url: str):
        payload = {"content": content}
        DiscordService._send(payload, webhook_url)

    @staticmethod
    def send_embed(embed: dict, webhook_url: str):
        DiscordService._send(embed, webhook_url)
