from typing import Dict

import disnake
from disnake.ext import commands

from database import Database
from models import SpawnSession
from services.card_service import (
    build_card_embed_and_file,
    build_spawn_embed_and_file,
)
from views.spawn_view import SpawnCardView

# yes its hard coded, and its temporary
# also most permanent solution is a temporary one
ADMIN_GUILD_ID = 1346993156335599676


def is_admin_guild_admin():
    async def predicate(inter: disnake.ApplicationCommandInteraction):
        # Optional guild restriction
        # if inter.guild is None or inter.guild.id != ADMIN_GUILD_ID:
        #     raise commands.CheckFailure(
        #         "These admin commands can only be used in the admin guild."
        #     )

        if not inter.author.guild_permissions.administrator:
            raise commands.CheckFailure(
                "You must be an administrator to use this command."
            )

        return True

    return commands.check(predicate)


class CardsCog(commands.Cog):
    def __init__(self, bot: commands.InteractionBot, db: Database):
        self.bot = bot
        self.db = db
        self.active_spawns: Dict[int, SpawnSession] = {}
        self.active_views: Dict[int, SpawnCardView] = {}

    # =========================================================
    # GLOBAL ERROR HANDLER
    # =========================================================

    @commands.Cog.listener()
    async def on_slash_command_error(
        self,
        inter: disnake.ApplicationCommandInteraction,
        error
    ):
        if isinstance(error, commands.CheckFailure):
            if inter.response.is_done():
                await inter.followup.send(
                    str(error),
                    ephemeral=True
                )
            else:
                await inter.response.send_message(
                    str(error),
                    ephemeral=True
                )
            return

        # Optional generic fallback
        if inter.response.is_done():
            await inter.followup.send(
                "An unexpected error occurred.",
                ephemeral=True
            )
        else:
            await inter.response.send_message(
                "An unexpected error occurred.",
                ephemeral=True
            )

        raise error

    # =========================================================
    # AUTOCOMPLETE
    # =========================================================

    async def card_autocomplete(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user_input: str
    ):
        text = user_input.strip()

        if not text:
            return self.db.list_all_card_names(limit=25)

        return self.db.search_card_names(text, limit=25)

    # =========================================================
    # SPAWN MESSAGE
    # =========================================================

    async def create_spawn_message(
        self,
        inter: disnake.ApplicationCommandInteraction,
        card_obj
    ):
        embed, file = await build_spawn_embed_and_file(card_obj)

        embed.title = "🃏 A wild card appeared!"
        embed.description = (
            "Press **Catch** and type the exact card name to claim it.\n\n"
            f"**Hints**\n"
            f"ATK: {card_obj.attack} {card_obj.attack_boost}\n"
            f"HP: {card_obj.health} {card_obj.health_boost}\n"
            f"Rarity: {card_obj.rarity}"
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

    # =========================================================
    # ROOT COMMANDS
    # =========================================================

    @commands.slash_command(
        name="battle",
        description="Main command for all card battle features."
    )
    async def battle(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @commands.slash_command(
        name="admin",
        description="Main command for all card admin features."
    )
    @is_admin_guild_admin()
    async def admin(self, inter: disnake.ApplicationCommandInteraction):
        pass

    # =========================================================
    # /battle info
    # =========================================================

    @battle.sub_command(
        name="info",
        description="Display information about a card."
    )
    async def info(
        self,
        inter: disnake.ApplicationCommandInteraction,
        card: str = commands.Param(
            description="Choose a card",
            autocomplete=card_autocomplete
        )
    ):
        card_obj = self.db.get_card_by_name(card)

        if not card_obj:
            await inter.response.send_message(
                f"Card `{card}` was not found.",
                ephemeral=True
            )
            return

        embed, file = await build_card_embed_and_file(card_obj)

        if file:
            await inter.response.send_message(embed=embed, file=file)
        else:
            await inter.response.send_message(embed=embed)

    # =========================================================
    # /admin spawn
    # =========================================================

    @admin.sub_command(
        name="spawn",
        description="Spawn a specific card."
    )
    async def spawn(
        self,
        inter: disnake.ApplicationCommandInteraction,
        card: str = commands.Param(
            description="Choose a card to spawn",
            autocomplete=card_autocomplete,
            default=None
        ),
    ):
        await inter.response.defer()

        if card is not None:
            card_obj = self.db.get_card_by_name(card)

            if not card_obj:
                await inter.edit_original_response(
                    content=f"Card `{card}` was not found."
                )
                return

            await self.create_spawn_message(inter, card_obj)

        else:
            card_obj = self.db.get_random_card_by_rarity()

            if not card_obj:
                await inter.edit_original_response(
                    content="No cards are available to spawn."
                )
                return

            await self.create_spawn_message(inter, card_obj)

    # =========================================================
    # /admin give
    # =========================================================

    @admin.sub_command(
        name="give",
        description="Give a card to a user."
    )
    async def admin_give(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            description="User to give the card to"
        ),
        card: str = commands.Param(
            description="Card to give",
            autocomplete=card_autocomplete
        ),
        quantity: int = commands.Param(
            default=1,
            ge=1,
            le=100,
            description="Amount to give"
        )
    ):
        if user.bot:
            await inter.response.send_message(
                "You cannot give cards to bots.",
                ephemeral=True
            )
            return

        if user.id == inter.author.id:
            await inter.response.send_message(
                "You cannot give cards to yourself.",
                ephemeral=True
            )
            return

        card_obj = self.db.get_card_by_name(card)

        if not card_obj:
            await inter.response.send_message(
                f"Card `{card}` was not found.",
                ephemeral=True
            )
            return

        # FIXED: give card to target user instead of admin
        success = self.db.add_card_to_inventory(
            user.id,
            card_obj.id,
            quantity
        )

        if not success:
            await inter.response.send_message(
                "An unknown error occurred while giving the card.",
                ephemeral=True
            )
            return

        await inter.response.send_message(
            f"🎁 {inter.author.mention} *ADMIN* gave "
            f"**✈︎ {card_obj.name}** × {quantity} "
            f"to {user.mention}."
        )

    # =========================================================
    # /battle inventory
    # =========================================================

    @battle.sub_command(
        name="inventory",
        description="View your inventory or another user's inventory."
    )
    async def inventory(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            default=None,
            description="User to inspect"
        )
    ):
        target = user or inter.author

        items = self.db.get_user_inventory(target.id)

        if not items:
            await inter.response.send_message(
                f"📦 {target.mention} has no cards in their inventory.",
                ephemeral=False
            )
            return

        embed = disnake.Embed(
            title=f"{target.display_name}'s Card Inventory",
            color=disnake.Color.gold()
        )

        embed.description = "\n".join(
            f"• **{name}** × {qty}"
            for name, qty in items[:50]
        )

        await inter.response.send_message(embed=embed)

    # =========================================================
    # /battle give
    # =========================================================

    @battle.sub_command(
        name="give",
        description="Gift a card to another user."
    )
    async def give(
        self,
        inter: disnake.ApplicationCommandInteraction,
        user: disnake.User = commands.Param(
            description="User to gift the card to"
        ),
        card: str = commands.Param(
            description="Card to gift",
            autocomplete=card_autocomplete
        ),
        quantity: int = commands.Param(
            default=1,
            ge=1,
            le=100,
            description="Amount to gift"
        )
    ):
        if user.bot:
            await inter.response.send_message(
                "You cannot gift cards to bots.",
                ephemeral=True
            )
            return

        if user.id == inter.author.id:
            await inter.response.send_message(
                "You cannot gift cards to yourself.",
                ephemeral=True
            )
            return

        card_obj = self.db.get_card_by_name(card)

        if not card_obj:
            await inter.response.send_message(
                f"Card `{card}` was not found.",
                ephemeral=True
            )
            return

        success = self.db.transfer_card(
            inter.author.id,
            user.id,
            card_obj.id,
            quantity
        )

        if not success:
            await inter.response.send_message(
                f"You do not own enough copies of "
                f"**✈︎ {card_obj.name}**.",
                ephemeral=True
            )
            return

        await inter.response.send_message(
            f"🎁 {inter.author.mention} gave "
            f"**✈︎ {card_obj.name}** × {quantity} "
            f"to {user.mention}."
        )

    # =========================================================
    # /battle all
    # =========================================================

    @battle.sub_command(
        name="all",
        description="Display every card."
    )
    async def all_cards(
        self,
        inter: disnake.ApplicationCommandInteraction
    ):
        cards = self.db.list_all_card_names(limit=9999)

        if not cards:
            await inter.response.send_message(
                "No cards were found.",
                ephemeral=True
            )
            return

        for i, card in enumerate(cards):
            card_obj = self.db.get_card_by_name(card)

            if not card_obj:
                msg = f"Card `{card}` was not found."

                if i == 0 and not inter.response.is_done():
                    await inter.response.send_message(
                        msg,
                        ephemeral=True
                    )
                else:
                    await inter.followup.send(
                        msg,
                        ephemeral=True
                    )

                continue

            embed, file = await build_card_embed_and_file(card_obj)

            if i == 0:
                if file:
                    await inter.response.send_message(
                        embed=embed,
                        file=file
                    )
                else:
                    await inter.response.send_message(embed=embed)

            else:
                if file:
                    await inter.followup.send(
                        embed=embed,
                        file=file
                    )
                else:
                    await inter.followup.send(embed=embed)