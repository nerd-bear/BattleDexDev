from typing import Dict
import disnake
from disnake.ext import commands
from database import Database
from models import SpawnSession
from services.card_service import build_card_embed_and_file, build_spawn_embed_and_file
from views.spawn_view import SpawnCardView

class CardsCog(commands.Cog):
    def __init__(self, bot: commands.InteractionBot, db: Database):
        self.bot = bot
        self.db = db
        self.active_spawns: Dict[int, SpawnSession] = {}
        self.active_views: Dict[int, SpawnCardView] = {}

    async def card_autocomplete(
        self, inter: disnake.ApplicationCommandInteraction, user_input: str
    ):
        if not user_input.strip():
            return self.db.list_all_card_names(limit=9999)
        return self.db.search_card_names(user_input, limit=9999)

    async def create_spawn_message(
        self, inter: disnake.ApplicationCommandInteraction, card_obj
    ):
        embed, file = await build_spawn_embed_and_file(card_obj)
        embed.title = '🃏 A wild card appeared!'
        embed.description = (
            'Press **Catch** and type the exact card name to claim it.\n\n'
            f'**Hints**\n'
            f'ATK: {card_obj.attack} {card_obj.attack_boost}'.strip() + '\n'
            f'HP: {card_obj.health} {card_obj.health_boost}'.strip() + '\n'
            f'Rarity: {card_obj.rarity:g}'
        )
        
        if file:
            await inter.edit_original_response(embed=embed, file=file)
        else:
            await inter.edit_original_response(embed=embed)
            
        message = await inter.original_message()
        session = SpawnSession(
            message_id=message.id,
            channel_id=message.channel.id,
            card_id=card_obj.id,
            card_name=card_obj.name
        )
        self.active_spawns[message.id] = session
        view = SpawnCardView(self, session)
        view.message = message
        self.active_views[message.id] = view
        await message.edit(view=view)

    @commands.slash_command(name='battle', description='Main command for all card battle features.')
    async def battle(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @battle.sub_command(name='info', description='Display information about a card.')
    async def info(
        self, inter: disnake.ApplicationCommandInteraction, 
        card: str = commands.Param(
            description='Choose a card', 
            autocomplete=card_autocomplete
        )
    ):
        card_obj = self.db.get_card_by_name(card)
        if not card_obj:
            await inter.response.send_message(
                f'Card {card} was not found.', ephemeral=True
            )
            return
            
        embed, file = await build_card_embed_and_file(card_obj)
        if file:
            await inter.response.send_message(embed=embed, file=file)
        else:
            await inter.response.send_message(embed=embed)

    @battle.sub_command(name='spawn', description='Spawn a specific card that users can catch.')
    async def spawn(
        self, inter: disnake.ApplicationCommandInteraction, 
        card: str = commands.Param(
            description='Choose a card to spawn', 
            autocomplete=card_autocomplete
        )
    ):
        await inter.response.defer()
        card_obj = self.db.get_card_by_name(card)
        if not card_obj:
            await inter.edit_original_response(
                content=f'Card {card} was not found.'
            )
            return
        await self.create_spawn_message(inter, card_obj)

    @battle.sub_command(
        name='spawn_random', description='Spawn a random card using rarity-weighted odds.'
    )
    async def spawn_random(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer()
        card_obj = self.db.get_random_card_by_rarity()
        if not card_obj:
            await inter.edit_original_response(
                content='No cards are available to spawn.'
            )
            return
        await self.create_spawn_message(inter, card_obj)

    @battle.sub_command(name='inventory', description="View your inventory or another user's inventory.")
    async def inventory(
        self, inter: disnake.ApplicationCommandInteraction, 
        user: disnake.User = commands.Param(default=None, description='User to inspect')
    ):
        target = user or inter.author
        items = self.db.get_user_inventory(target.id)
        if not items:
            await inter.response.send_message(
                f'📦 {target.mention} has no cards in their inventory.', ephemeral=False
            )
            return
            
        embed = disnake.Embed(
            title=f"{target.display_name}'s Card Inventory", 
            color=disnake.Color.gold()
        )
        embed.description = '\n'.join(
            f'• **{name}** × {qty}' for name, qty in items[:50]
        )
        await inter.response.send_message(embed=embed)

    @battle.sub_command(name='give', description='Gift a card to another user.')
    async def give(
        self, inter: disnake.ApplicationCommandInteraction, 
        user: disnake.User = commands.Param(description='User to gift the card to'), 
        card: str = commands.Param(
            description='Card to gift', 
            autocomplete=card_autocomplete
        ), 
        quantity: int = commands.Param(default=1, ge=1, le=100, description='Amount to gift')
    ):
        if user.bot:
            await inter.response.send_message(
                'You cannot gift cards to bots.', ephemeral=True
            )
            return
        if user.id == inter.author.id:
            await inter.response.send_message(
                'You cannot gift cards to yourself.', ephemeral=True
            )
            return
            
        card_obj = self.db.get_card_by_name(card)
        if not card_obj:
            await inter.response.send_message(
                f'Card {card} was not found.', ephemeral=True
            )
            return
            
        success = self.db.transfer_card(inter.author.id, user.id, card_obj.id, quantity)
        if not success:
            await inter.response.send_message(
                f'You do not own enough copies of **✈︎ {card_obj.name}**.', ephemeral=True
            )
            return
            
        await inter.response.send_message(
            f'🎁 {inter.author.mention} gave **✈︎ {card_obj.name}** × {quantity} to {user.mention}.'
        )

    @battle.sub_command(name='all', description='Display every card.')
    async def all_cards(
        self,
        inter: disnake.ApplicationCommandInteraction,
    ):
        cards = self.db.list_all_card_names()

        for i, card in enumerate(cards):
            card_obj = self.db.get_card_by_name(card)
            if not card_obj:
                msg = f'Card {card} was not found.'
                if i == 0 and not inter.response.is_done():
                    await inter.response.send_message(msg, ephemeral=True)
                else:
                    await inter.followup.send(msg, ephemeral=True)
                return

            embed, file = await build_card_embed_and_file(card_obj)

            if i == 0:
                if file:
                    await inter.response.send_message(embed=embed, file=file)
                else:
                    await inter.response.send_message(embed=embed)
            else:
                if file:
                    await inter.followup.send(embed=embed, file=file)
                else:
                    await inter.followup.send(embed=embed)