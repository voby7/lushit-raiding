# token_raid.py cog
# Let's users start raids with user tokens
# Controled via modal menu
# Requires the token to be valid and have the correct permissions in the target server

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
import aiohttp
import asyncio
from utils.raid_logger import rlog
from utils.raid_config import MAIN_GUILD, SERVER_INVITE

from utils.access_manager import AccessManager
access = AccessManager()

class TokenRaidModal(Modal, title="Token Raid"):
    token = TextInput(label="Discord Token", placeholder="Enter your Discord token here", required=True)
    message = TextInput(label="Message to Spam", placeholder="Enter the message to spam", required=True)
    count = TextInput(label="Number of Messages", placeholder="Number of messages to send (1-100)", required=True)
    delay = TextInput(label="Delay Between Messages", placeholder="Delay in seconds (0.5-5)", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        token = self.token.value
        message = self.message.value

        try:
            count = int(self.count.value)
            delay = float(self.delay.value)
            if count < 1 or count > 100:
                await interaction.followup.send("Count must be between 1 and 100.", ephemeral=True)
                return
            if delay < 0.5 or delay > 5:
                await interaction.followup.send("Delay must be between 0.5 and 5 seconds.", ephemeral=True)
                return

            headers = {
                "Authorization": token,
                "Content-Type": "application/json"
            }
            channel_id = interaction.channel_id
            url = f"https://discord.com/api/v9/channels/{channel_id}/messages"

            async with aiohttp.ClientSession() as session:
                for i in range(count):
                    async with session.post(url, headers=headers, json={"content": message}) as resp:
                        if resp.status == 429: # Rate limited
                            data = await resp.json()
                            wait = data.get("retry_after", 1)
                            await asyncio.sleep(wait)
                        elif resp.status != 200 and resp.status != 204:
                            await interaction.followup.send(f"Error at message {i+1}: HTTP {resp.status}", ephemeral=True)
                            return
                    await asyncio.sleep(delay)

            await interaction.followup.send(f"Successfully sent {count} messages with provided token.", ephemeral=True)
        except ValueError:
            await interaction.followup.send("Invalid count or delay format.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An unexpected error occurred: {e}", ephemeral=True)

class TokenRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="token_raid", description="Raid a channel using a custom user token")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def token_raid(self, interaction: discord.Interaction):
        await rlog(self.bot, "token_raid", interaction.user, interaction.guild_id)
        # Guard check
        guard = await access.guard(interaction, {"action": "token_raid", "cooldown_seconds": 60})
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

        await interaction.response.send_modal(TokenRaidModal())

async def setup(bot):
    await bot.add_cog(TokenRaid(bot))
