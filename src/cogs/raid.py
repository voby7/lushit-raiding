import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import asyncio
import random
from utils.access_manager import AccessManager
from utils.raid_config import RAID_MESSAGE, MAX_MESSAGES, MAIN_GUILD, SERVER_INVITE
from utils.raid_logger import rlog

access = AccessManager()

allowed_mentions = discord.AllowedMentions(everyone=True)

# ===================================
# Raid Button View
# ===================================
class RaidButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Send Raid Burst", style=discord.ButtonStyle.danger)
    async def send_raid(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        for i in range(5):
            try:
                await interaction.followup.send(f"{RAID_MESSAGE}")
                await asyncio.sleep(random.uniform(0.5, 1.5))
            except Exception as e:
                print(f"Error sending raid message: {e}")

class LagRaidButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Trigger Lag Burst", style=discord.ButtonStyle.danger)
    async def lag_burst(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        emoji_block = "💥" * 100
        zalgo = "𝖘𝖕𝖆𝖒" * 50
        filler = "LAG" * 300
        payload = f"{emoji_block}\n{zalgo}\n{filler}\n{emoji_block}"
        for i in range(5):
            try:
                await interaction.followup.send(f"{payload}")
                await asyncio.sleep(random.uniform(0.5, 1.0))
            except Exception as e:
                print(f"Error sending lag burst: {e}")

# ===================================
# Raid Commands
# ===================================
class RaidCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="raid", description="Send a burst of messages")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def raid(self, interaction: discord.Interaction, count: int = 5):
        await rlog(self.bot, "raid", interaction.user, interaction.guild_id)
        # Guard check
        guard = await access.guard(interaction, {"action": "raid", "cooldown_seconds": 60})
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
        count = max(1, min(count, MAX_MESSAGES))
        await interaction.response.send_message(f"Sending {count} message(s)...", ephemeral=True)
        for i in range(min(count, 5)):
            await interaction.followup.send(f"{RAID_MESSAGE}")
            await asyncio.sleep(1)

    @app_commands.command(name="b-raid", description="Button-based raid")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def b_raid(self, interaction: discord.Interaction):
        await rlog(self.bot, "b-raid", interaction.user, interaction.guild_id)
        # Guard check
        guard = await access.guard(interaction, {"action": "b-raid", "cooldown_seconds": 60})
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
        await interaction.response.send_message("Click the button to start raiding!", view=RaidButtonView(), ephemeral=True)

    @app_commands.command(name="slow-raid", description="Send slow, spaced-out raid messages")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def slow_raid(self, interaction: discord.Interaction, count: int = 5):
        await rlog(self.bot, "slow-raid", interaction.user, interaction.guild_id)
        # Guard check
        guard = await access.guard(interaction, {"action": "slow-raid", "cooldown_seconds": 60})
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
        count = max(1, min(count, MAX_MESSAGES))
        await interaction.response.send_message(f"Sending {count} slow messages...", ephemeral=True)
        for i in range(count):
            await interaction.followup.send(f"{RAID_MESSAGE}")
            await asyncio.sleep(random.uniform(8, 15))

    @app_commands.command(name="unicode-raid", description="Send Unicode-abuse messages")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def unicode_raid(self, interaction: discord.Interaction, count: int = 5):
        await rlog(self.bot, "unicode-raid", interaction.user, interaction.guild_id)
        # Guard check
        guard = await access.guard(interaction, {"action": "unicode-raid", "cooldown_seconds": 60})
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
        zalgo = "𝖘𝖕𝖆𝖒" * 50
        fullwidth = "ＦＲＥＥ ＮＩＴＲＯ ＨＥＲＥ"
        chaos = f"{zalgo}\n{fullwidth}\n🚨🚨🚨"
        count = max(1, min(count, MAX_MESSAGES))
        await interaction.response.send_message(f"Sending {count} Unicode raid messages...", ephemeral=True)
        for i in range(count):
            await interaction.followup.send(f"{chaos}")
            await asyncio.sleep(1)

    @app_commands.command(name="lag-raid", description="Send large, intense messages")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def lag_raid(self, interaction: discord.Interaction, count: int = 5):
        await interaction.response.defer(ephemeral=True)
        await rlog(self.bot, "lag-raid", interaction.user, interaction.guild_id)
        # Guard check
        guard = await access.guard(interaction, {"action": "lag-raid", "cooldown_seconds": 60})
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
            return await interaction.followup.send(view=view, ephemeral=True)
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
                return await interaction.followup.send(view=view, ephemeral=True)
        # End of checks
        count = max(1, min(count, MAX_MESSAGES))
        await interaction.followup.send(f"Sending {count} lag-style messages...", ephemeral=True)
        emoji_block = "💥" * 100
        zalgo = "𝖘𝖕𝖆𝖒" * 50
        filler = "LAG" * 300
        payload = f"{emoji_block}\n{zalgo}\n{filler}\n{emoji_block}"
        for i in range(count):
            try:
                await interaction.followup.send(f"{payload}")
                await asyncio.sleep(random.uniform(0.5, 1.0))
            except Exception as e:
                print(f"Failed to send lag message: {e}")

    @app_commands.command(name="b-lag-raid", description="Button-based lag simulation")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def b_lag_raid(self, interaction: discord.Interaction):
        await rlog(self.bot, "b-lag-raid", interaction.user, interaction.guild_id)
        # Guard check
        guard = await access.guard(interaction, {"action": "b-lag-raid", "cooldown_seconds": 60})
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
        await interaction.response.send_message("Click the button to trigger a lag burst:", view=LagRaidButtonView(), ephemeral=True)

async def setup(bot):
    await bot.add_cog(RaidCog(bot))
