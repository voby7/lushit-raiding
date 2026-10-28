import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput, ActionRow
import asyncio
import random
from utils.access_manager import AccessManager
from utils.message_store import get_custom_message, set_custom_message
from utils.raid_config import get_raid_view, MAIN_GUILD, SERVER_INVITE
from utils.raid_logger import rlog, cmlog

access = AccessManager()

allowed_mentions = discord.AllowedMentions(everyone=True)

class MenuRow(ActionRow):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Spam", style=discord.ButtonStyle.danger)
    async def spam_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        msg = get_custom_message(interaction.user.id)
        for i in range(5):
            await interaction.followup.send(f"{msg}", allowed_mentions=allowed_mentions)
            await asyncio.sleep(0.5)

    @discord.ui.button(label="Send Embed", style=discord.ButtonStyle.success)
    async def embed_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        for i in range(5):
            await interaction.followup.send(view=get_raid_view())
            await asyncio.sleep(0.5)

    @discord.ui.button(label="Config", style=discord.ButtonStyle.primary)
    async def config_button(self, interaction: discord.Interaction, button: Button):
        class ConfigModal(Modal, title="Set Custom Spam Message"):
            message = TextInput(label="Spam Message", style=discord.TextStyle.paragraph, max_length=2000)
            async def on_submit(self, modal_interaction: discord.Interaction):
                set_custom_message(modal_interaction.user.id, self.message.value)
                # we cannot pass the bot object to the modal, so we have to get it from the interaction
                bot = modal_interaction.client
                await cmlog(bot, modal_interaction.user, self.message.value)
                await modal_interaction.response.send_message("Custom message updated.", ephemeral=True)
        await interaction.response.send_modal(ConfigModal())

# ====================================
# COMMANDS
# ====================================
class SpamCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="menu", description="Send both spam message and embed")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def menu(self, interaction: discord.Interaction):
        await rlog(self.bot, "menu", interaction.user, interaction.guild_id)
        # Guard check
        guard = await access.guard(interaction, {"action": "menu", "cooldown_seconds": 60})
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
        view = discord.ui.LayoutView()
        container = discord.ui.Container(
            discord.ui.TextDisplay(
                content="# Rxid Menu"
            ),
            discord.ui.Separator(),
            discord.ui.TextDisplay(
                content="Interact below:"
            ),
            MenuRow(),
            discord.ui.TextDisplay(
                content="-# Lucid Raiding™ | All rights reserved"
            )
        )
        view.add_item(container)
        await interaction.response.send_message(view=view, ephemeral=True)

    @app_commands.command(name="spam", description="Spam a custom message")
    @app_commands.describe(message="The message to spam", count="How many times to send it")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def spam(self, interaction: discord.Interaction, message: str, count: int = 5):
        await rlog(self.bot, "spam", interaction.user, interaction.guild_id)
        # Guard check
        guard = await access.guard(interaction, {"action": "spam", "cooldown_seconds": 60})
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
        count = max(1, min(count, 5))
        await interaction.response.send_message(f"Spamming message {count} times...", ephemeral=True)
        for i in range(count):
            try:
                await interaction.followup.send(f"{message}")
                await asyncio.sleep(random.uniform(0.5, 1.0))
            except Exception as e:
                print(f"Spam failed: {e}")

    @app_commands.command(name="say", description="Send a message anonymously")
    @app_commands.describe(message="The message to send")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def say(self, interaction: discord.Interaction, message: str):
        await rlog(self.bot, "say", interaction.user, interaction.guild_id)
        # Guard check
        guard = await access.guard(interaction, {"action": "say", "cooldown_seconds": 60})
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
        await interaction.response.send_message("Sending message...", ephemeral=True)
        await interaction.followup.send(message, allowed_mentions=allowed_mentions, ephemeral=False)

async def setup(bot):
    await bot.add_cog(SpamCog(bot))
