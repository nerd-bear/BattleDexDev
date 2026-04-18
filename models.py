from dataclasses import dataclass
from typing import Optional


@dataclass
class Card:
    id: int
    name: str
    attack: int
    health: int
    attack_boost: str
    health_boost: str
    rarity: float
    image: Optional[str]
    spawn_image: Optional[str]


@dataclass
class SpawnSession:
    message_id: int
    channel_id: int
    card_id: int
    card_name: str
    claimed_by: Optional[int] = None
