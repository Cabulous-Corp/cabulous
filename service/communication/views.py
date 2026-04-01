from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

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

        # Process the payload and return normalized data
        normalized_data = serializer.save()

        # Teste local para enviar a mensagem formatada para o Discord
        discord_webhook = "https://discord.com/api/webhooks/1486907560463175733/-z6AX_gtRfymX9xwURAgNyh8YRcI5Yzl95tc7VuniW4_-CdfCr1qn59Po1r7OUIMpqjN"
        post_to_discord(discord_webhook, dict(normalized_data))

        print(normalized_data)

        return Response(
            {"message": "Webhook received successfully", "data": normalized_data},
            status=status.HTTP_200_OK,
        )
