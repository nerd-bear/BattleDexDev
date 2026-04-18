import os
import re
from typing import Optional, Tuple

import disnake

from models import Card


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
        f"**Rarity:** {card.rarity:g}"
    )


async def build_card_embed_and_file(card: Card) -> Tuple[disnake.Embed, Optional[disnake.File]]:
    embed = disnake.Embed(
        title=card.name,
        description=build_card_text(card),
        color=disnake.Color.blurple()
    )

    if not card.image:
        return embed, None

    image_path = card.image

    if image_path.startswith('http://') or image_path.startswith('https://'):
        embed.set_image(url=image_path)
        return embed, None

    if os.path.exists(image_path):
        filename = os.path.basename(image_path)
        file = disnake.File(image_path, filename=filename)
        embed.set_image(url=f'attachment://{filename}')
        return embed, file

    return embed, None


async def build_spawn_embed_and_file(card: Card) -> Tuple[disnake.Embed, Optional[disnake.File]]:
    embed = disnake.Embed(
        title='🃏 A wild card appeared!',
        color=disnake.Color.orange()
    )

    image_path = card.spawn_image or card.image

    if not image_path:
        return embed, None

    if image_path.startswith('http://') or image_path.startswith('https://'):
        embed.set_image(url=image_path)
        return embed, None

    if os.path.exists(image_path):
        filename = os.path.basename(image_path)
        file = disnake.File(image_path, filename=filename)
        embed.set_image(url=f'attachment://{filename}')
        return embed, file

    return embed, None
