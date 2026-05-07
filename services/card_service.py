import disnake
import os
import re
from typing import Optional, Tuple
import disnake
from models import Card

DEFAULT_IMAGE_PATH = "./assets/cards/error_card.png"
DEFAULT_SPAWN_IMAGE_PATH = "./assets/cards/error_spawn.png"


def normalize_name(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r'[^a-z0-9]', '', value)
    return value


def build_card_text(card: Card) -> str:
    atk_text = f"{card.attack} {card.attack_boost}".strip()
    hp_text = f"{card.health} {card.health_boost}".strip()

    return (
        f"**ATK:** {atk_text}\n"
        f"**HP:** {hp_text}\n"
        f"**Rarity:** {card.rarity}"
    )

async def build_card_embed_and_file(card: Card) -> Tuple[disnake.Embed, Optional[disnake.File]]:
    embed = disnake.Embed(
        title=card.name,
        description=build_card_text(card),
        color=disnake.Color.blurple()
    )

    def attach_local_image(path: str):
        filename = os.path.basename(path)
        file = disnake.File(path, filename=filename)
        embed.set_image(url=f'attachment://{filename}')
        return embed, file

    image_path = card.image

    # no image provided 
    if not image_path:
        return attach_local_image(DEFAULT_IMAGE_PATH)

    # URL image
    if image_path.startswith(('http://', 'https://')):
        embed.set_image(url=image_path)
        return embed, None

    # file exists
    if os.path.exists(image_path):
        return attach_local_image(image_path)

    # smth else fails 
    if os.path.exists(DEFAULT_IMAGE_PATH):
        return attach_local_image(DEFAULT_IMAGE_PATH)

    return embed, None



async def build_spawn_embed_and_file(card: Card) -> Tuple[disnake.Embed, Optional[disnake.File]]:
    embed = disnake.Embed(
        title='🃏 A wild card appeared!',
        color=disnake.Color.orange()
    )

    def attach_local_image(path: str):
        filename = os.path.basename(path)
        file = disnake.File(path, filename=filename)
        embed.set_image(url=f'attachment://{filename}')
        return embed, file

    image_path = card.spawn_image or card.image

    # No image 
    if not image_path:
        if os.path.exists(DEFAULT_SPAWN_IMAGE_PATH):
            return attach_local_image(DEFAULT_SPAWN_IMAGE_PATH)
        return embed, None

    # URL
    if image_path.startswith(('http://', 'https://')):
        embed.set_image(url=image_path)
        return embed, None

    # file exists
    if os.path.exists(image_path):
        return attach_local_image(image_path)

   # smth else fails 
    if os.path.exists(DEFAULT_SPAWN_IMAGE_PATH):
        return attach_local_image(DEFAULT_SPAWN_IMAGE_PATH)

    return embed, None
