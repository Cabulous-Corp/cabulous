from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from communication.models import DiscordChannelPurpose
from communication.tasks import send_discord_channel_embed_by_purpose_task
from integrations.helpers import build_discord_embed
from integrations.serializer import GithubWebhookSerializer


class GithubWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request, *args: object, **kwargs: object) -> Response:
        event = request.headers.get("X-GitHub-Event")
        if not event:
            return Response(
                {"detail": "Missing X-GitHub-Event header."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = {
            "event": event,
            "payload": request.data,
        }

        serializer = GithubWebhookSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        normalized_data = serializer.save()

        embed = build_discord_embed(normalized_data)

        if embed is not None:
            send_discord_channel_embed_by_purpose_task.apply_async(
                kwargs={
                    "purpose": DiscordChannelPurpose.BOARD_UPDATES,
                    "embeds": [embed.model_dump(mode="json", exclude_none=True)],
                }
            )

        return Response(
            {"message": "Webhook received successfully", "data": normalized_data},
            status=status.HTTP_200_OK,
        )
