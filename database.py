import json
import random
import sqlite3
from contextlib import contextmanager
from typing import List, Optional, Tuple

from models import Card


class Database:
    def __init__(self, path: str):
        self.path = path

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def initialize(self):
        with self.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    attack INTEGER NOT NULL DEFAULT 0,
                    health INTEGER NOT NULL DEFAULT 0,
                    attack_boost TEXT NOT NULL DEFAULT '',
                    health_boost TEXT NOT NULL DEFAULT '',
                    rarity REAL NOT NULL DEFAULT 1,
                    image TEXT,
                    spawn_image TEXT
                )
            """)

            columns = {row['name'] for row in conn.execute('PRAGMA table_info(cards)').fetchall()}
            if 'rarity' not in columns:
                conn.execute("ALTER TABLE cards ADD COLUMN rarity REAL NOT NULL DEFAULT 1")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS inventories (
                    user_id INTEGER NOT NULL,
                    card_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (user_id, card_id),
                    FOREIGN KEY (card_id) REFERENCES cards(id)
                )
            """)

    def seed_from_json(self, json_path: str):
        with open(json_path, 'r', encoding='utf-8') as f:
            cards = json.load(f)

        with self.connect() as conn:
            for name, data in cards.items():
                rarity = float(data.get('rarity', 1))
                if rarity <= 0:
                    rarity = 1.0

                conn.execute("""
                    INSERT INTO cards (
                        name,
                        attack,
                        health,
                        attack_boost,
                        health_boost,
                        rarity,
                        image,
                        spawn_image
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                        attack=excluded.attack,
                        health=excluded.health,
                        attack_boost=excluded.attack_boost,
                        health_boost=excluded.health_boost,
                        rarity=excluded.rarity,
                        image=excluded.image,
                        spawn_image=excluded.spawn_image
                """, (
                    name,
                    int(data.get('attack', 0)),
                    int(data.get('health', 0)),
                    str(data.get('attack_boost', '')),
                    str(data.get('health_boost', '')),
                    rarity,
                    data.get('image'),
                    data.get('spawn_image')
                ))

    def _row_to_card(self, row: sqlite3.Row) -> Card:
        return Card(
            id=row['id'],
            name=row['name'],
            attack=row['attack'],
            health=row['health'],
            attack_boost=row['attack_boost'],
            health_boost=row['health_boost'],
            rarity=float(row['rarity'] or 1),
            image=row['image'],
            spawn_image=row['spawn_image']
        )

    def get_card_by_name(self, name: str) -> Optional[Card]:
        with self.connect() as conn:
            row = conn.execute("""
                SELECT * FROM cards WHERE LOWER(name) = LOWER(?)
            """, (name,)).fetchone()

        if not row:
            return None

        return self._row_to_card(row)

    def get_random_card_by_rarity(self) -> Optional[Card]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM cards").fetchall()

        if not rows:
            return None

        cards = [self._row_to_card(row) for row in rows]
        weights = []
        for card in cards:
            rarity = card.rarity if card.rarity > 0 else 1
            weights.append(1 / rarity)

        return random.choices(cards, weights=weights, k=1)[0]

    def search_card_names(self, text: str, limit: int = 25) -> List[str]:
        like = f"%{text.lower()}%"
        with self.connect() as conn:
            rows = conn.execute("""
                SELECT name
                FROM cards
                WHERE LOWER(name) LIKE ?
                ORDER BY name
                LIMIT ?
            """, (like, limit)).fetchall()

        return [row['name'] for row in rows]

    def list_all_card_names(self, limit: int = 25) -> List[str]:
        with self.connect() as conn:
            rows = conn.execute("""
                SELECT name FROM cards ORDER BY name LIMIT ?
            """, (limit,)).fetchall()

        return [row['name'] for row in rows]

    def add_card_to_inventory(self, user_id: int, card_id: int, quantity: int = 1):
        with self.connect() as conn:
            conn.execute("""
                INSERT INTO inventories (user_id, card_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, card_id) DO UPDATE SET
                    quantity = quantity + excluded.quantity
            """, (user_id, card_id, quantity))

    def get_user_inventory(self, user_id: int) -> List[Tuple[str, int]]:
        with self.connect() as conn:
            rows = conn.execute("""
                SELECT c.name, i.quantity
                FROM inventories i
                JOIN cards c ON c.id = i.card_id
                WHERE i.user_id = ? AND i.quantity > 0
                ORDER BY c.name
            """, (user_id,)).fetchall()

        return [(row['name'], row['quantity']) for row in rows]

    def user_has_card(self, user_id: int, card_id: int, quantity: int = 1) -> bool:
        with self.connect() as conn:
            row = conn.execute("""
                SELECT quantity
                FROM inventories
                WHERE user_id = ? AND card_id = ?
            """, (user_id, card_id)).fetchone()

        return bool(row and row['quantity'] >= quantity)

    def transfer_card(self, from_user_id: int, to_user_id: int, card_id: int, quantity: int = 1) -> bool:
        with self.connect() as conn:
            row = conn.execute("""
                SELECT quantity
                FROM inventories
                WHERE user_id = ? AND card_id = ?
            """, (from_user_id, card_id)).fetchone()

            if not row or row['quantity'] < quantity:
                return False

            conn.execute("""
                UPDATE inventories
                SET quantity = quantity - ?
                WHERE user_id = ? AND card_id = ?
            """, (quantity, from_user_id, card_id))

            conn.execute("""
                INSERT INTO inventories (user_id, card_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, card_id) DO UPDATE SET
                    quantity = quantity + excluded.quantity
            """, (to_user_id, card_id, quantity))

            conn.execute("""
                DELETE FROM inventories
                WHERE user_id = ? AND card_id = ? AND quantity <= 0
            """, (from_user_id, card_id))

            return True
