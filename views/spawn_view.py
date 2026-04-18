import time

import disnake

from models import SpawnSession
from services.card_service import normalize_name


class CatchCardModal(disnake.ui.Modal):
    def __init__(self, cog, session: SpawnSession):
        self.cog = cog
        self.session = session

        components = [
            disnake.ui.TextInput(
                label="Card name",
                placeholder="Type the exact card name",
                custom_id="card_name",
                style=disnake.TextInputStyle.short,
                max_length=100
            )
        ]

        super().__init__(
            title="Catch the Card",
            custom_id=f"catch_card_modal:{session.message_id}",
            components=components
        )

    async def callback(self, inter: disnake.ModalInteraction):
        active = self.cog.active_spawns.get(self.session.message_id)
        if not active:
            await inter.response.send_message(
                "This card spawn is no longer active.",
                ephemeral=True
            )
            return

        if active.claimed_by is not None:
            await inter.response.send_message(
                "This card has already been caught.",
                ephemeral=True
            )
            return

        answer = inter.text_values["card_name"]
        if normalize_name(answer) != normalize_name(active.card_name):
            await inter.response.send_message(
                "Wrong card name. Try again if nobody catches it first.",
                ephemeral=True
            )
            return

        # 1. Update the database
        self.cog.db.add_card_to_inventory(inter.author.id, active.card_id, 1)
        active.claimed_by = inter.author.id

        # 2. Stop the active view
        view = self.cog.active_views.get(self.session.message_id)
        if view:
            view.stop()

        # 3. Create a brand NEW view that only contains a dead button.
        # This completely avoids Discord component syncing bugs.
        disabled_view = disnake.ui.View()
        disabled_view.add_item(
            disnake.ui.Button(label="Catch", style=disnake.ButtonStyle.secondary, disabled=True)
        )

        # 4. Fetch the message reliably
        message = inter.message or (view.message if view else None)

        if message and message.embeds:
            embed = message.embeds[0]
            embed.color = disnake.Color.green()
            embed.title = f"✅ {active.card_name} was caught!"
            embed.description = f"Caught by {inter.author.mention}"

            if embed.image and embed.image.url:
                url = embed.image.url
                if url.startswith("attachment://") or "cdn.discordapp.com" in url or "media.discordapp.net" in url:
                    filename = url.split("/")[-1].split("?")[0]
                    embed.set_image(url=f"attachment://{filename}")

            # Edit the message with the new disabled_view
            await message.edit(embed=embed, view=disabled_view)

        await inter.response.send_message(
            f"{inter.author.mention} just caught the **{active.card_name}** card!",
        )

        self.cog.active_spawns.pop(self.session.message_id, None)
        self.cog.active_views.pop(self.session.message_id, None)

    async def on_error(self, error: Exception, inter: disnake.ModalInteraction) -> None:
        if inter.response.is_done():
            await inter.followup.send(
                f"Something went wrong: `{error}`",
                ephemeral=True
            )
        else:
            await inter.response.send_message(
                f"Something went wrong: `{error}`",
                ephemeral=True
            )


class SpawnCardView(disnake.ui.View):
    def __init__(self, cog, session: SpawnSession, timeout: float = 60):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.session = session
        self.created_at = time.time()
        self.message = None

    @disnake.ui.button(label="Catch", style=disnake.ButtonStyle.green)
    async def catch_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        active = self.cog.active_spawns.get(self.session.message_id)
        if not active:
            await inter.response.send_message(
                "This card spawn is no longer active.",
                ephemeral=True
            )
            return

        if active.claimed_by is not None:
            await inter.response.send_message(
                "This card has already been caught.",
                ephemeral=True
            )
            return

        await inter.response.send_modal(CatchCardModal(self.cog, active))

    async def on_timeout(self):
        active = self.cog.active_spawns.get(self.session.message_id)

        if not active or active.claimed_by is not None:
            self.cog.active_spawns.pop(self.session.message_id, None)
            self.cog.active_views.pop(self.session.message_id, None)
            return

        self.cog.active_spawns.pop(self.session.message_id, None)
        
        # Nuke existing items and slap a dead button in its place
        self.clear_items()
        self.add_item(
            disnake.ui.Button(label="Catch", style=disnake.ButtonStyle.secondary, disabled=True)
        )

        try:
            if self.message and self.message.embeds:
                embed = self.message.embeds[0]
                embed.color = disnake.Color.red()
                embed.title = "⌛ Card expired"
                embed.description = "Nobody caught this card in time."

                if embed.image and embed.image.url:
                    url = embed.image.url
                    if url.startswith("attachment://") or "cdn.discordapp.com" in url or "media.discordapp.net" in url:
                        filename = url.split("/")[-1].split("?")[0]
                        embed.set_image(url=f"attachment://{filename}")

                # Edit with the newly updated self (which now only has a disabled button)
                await self.message.edit(embed=embed, view=self)
        except Exception:
            pass

        self.cog.active_views.pop(self.session.message_id, None)