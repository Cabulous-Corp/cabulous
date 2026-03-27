import json
import os
import sys
from django.test import TestCase
from services.discord import DiscordService as discord

if __package__ in (None, ""):
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_send_default_welcome_message():
    # Simulate sending a welcome message to a new user
    with open("communication/templates/discord/d_bem_vindo.json") as f:
        welcome_message = json.load(f)
    try:
        discord.send_message(
            content=welcome_message["content"],
            webhook_url="https://discord.com/api/webhooks/1486097706198765699/f1PNruEtUuEhQ27x9STjlGApLcumIO02j_hbcqlQETzl4gn6r7EpMMAvkFrSyF5v5Ufb",
        )
        result = "Message sent successfully"
    except Exception as e:
        result = f"Failed to send message: {e}"
    print(result)


def test_send_embed_message():
    # Simulate sending an embed message to a new user
    with open("communication/templates/discord/embed_bem_vindo.json") as f:
        embed_message = json.load(f)
    try:
        discord.send_embed(
            embed=embed_message,
            webhook_url="https://discord.com/api/webhooks/1486097706198765699/f1PNruEtUuEhQ27x9STjlGApLcumIO02j_hbcqlQETzl4gn6r7EpMMAvkFrSyF5v5Ufb",
        )
        result = "Embed message sent successfully"
    except Exception as e:
        result = f"Failed to send embed message: {e}"
    print(result)


test_send_default_welcome_message()
test_send_embed_message()
