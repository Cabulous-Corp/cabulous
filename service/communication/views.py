from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from communication.helpers.discord_channel import DiscordChannelHelper
from communication.models import DiscordChannelPurpose
from communication.serializer import GithubWebhookSerializer
from communication.webhookhelper import post_to_discord


class GithubWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
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

        try:
            discord_webhook = DiscordChannelHelper.get_webhook_url_by_purpose(
                DiscordChannelPurpose.BOARD_UPDATES
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        post_to_discord(discord_webhook, dict(normalized_data))

        return Response(
            {"message": "Webhook received successfully", "data": normalized_data},
            status=status.HTTP_200_OK,
        )
