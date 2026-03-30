from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class DiscordEmbedFooter(BaseModel):
    text: str
    icon_url: HttpUrl | None = None


class DiscordEmbedImage(BaseModel):
    url: HttpUrl


class DiscordEmbedThumbnail(BaseModel):
    url: HttpUrl


class DiscordEmbedAuthor(BaseModel):
    name: str
    url: HttpUrl | None = None
    icon_url: HttpUrl | None = None


class DiscordEmbedField(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    value: str = Field(min_length=1, max_length=1024)
    inline: bool = False


class DiscordEmbed(BaseModel):
    title: str | None = Field(default=None, max_length=256)
    description: str | None = Field(default=None, max_length=4096)
    color: int | None = None
    url: HttpUrl | None = None
    timestamp: str | None = None
    footer: DiscordEmbedFooter | None = None
    image: DiscordEmbedImage | None = None
    thumbnail: DiscordEmbedThumbnail | None = None
    author: DiscordEmbedAuthor | None = None
    fields: list[DiscordEmbedField] | None = None


class DiscordWebhookPayload(BaseModel):
    content: str | None = None
    embeds: list[DiscordEmbed]

    model_config = ConfigDict(extra="forbid")
