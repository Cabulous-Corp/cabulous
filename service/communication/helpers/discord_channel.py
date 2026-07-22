from communication.models import DiscordChannel, DiscordChannelPurpose


class DiscordChannelHelper:
    @staticmethod
    def get_active_channel_by_purpose(
        purpose: DiscordChannelPurpose | str,
    ) -> DiscordChannel:
        channel = DiscordChannel.objects.filter(
            purpose=str(purpose),
            is_active=True,
        ).first()
        if channel is None:
            raise ValueError(f"No active Discord channel configured for purpose '{purpose}'.")
        return channel

    @staticmethod
    def get_webhook_url_by_purpose(
        purpose: DiscordChannelPurpose | str,
    ) -> str:
        channel = DiscordChannelHelper.get_active_channel_by_purpose(purpose)
        return channel.webhook_url
