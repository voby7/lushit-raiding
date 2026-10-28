# webhook_raid.py cog
# Webhook-based raid functionality
# Opens a modal to configure the raid, then sends messages via webhook
# Requires the user to provide a webhook URL
# Also I will not be updating this again any time soon because it works and that is all that fucking matters and anyone who disagrees with that can fuck off and go die in a fucking hole

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput
import aiohttp
import asyncio

from utils.access_manager import AccessManager
from utils.raid_config import LOGO_URL, SERVER_INVITE
from utils.raid_logger import rlog

access = AccessManager()

webhook_name = "Lucid Raiding™"
webhook_avatar = LOGO_URL

class WebhookRaidModal(Modal, title="Webhook Raid Configuration"):
    webhook_url = TextInput(label="Webhook URL", placeholder="https://discord.com/api/webhooks/...", required=True)
    message = TextInput(label="Message", placeholder="Type your raid message here...", required=True, style=discord.TextStyle.paragraph)
    count = TextInput(label="Count", placeholder="Number of messages (1-100)", required=True)
    delay = TextInput(label="Delay (seconds)", placeholder="Delay between messages (0.1-10)", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            webhook_url = self.webhook_url.value
            message = self.message.value
            count = int(self.count.value)
            delay = float(self.delay.value)
            if count < 1 or count > 100:
                await interaction.followup.send("Count must be between 1 and 100.", ephemeral=True)
                return
            if delay < 0.1 or delay > 10:
                await interaction.followup.send("Delay must be between 0.1 and 10 seconds.", ephemeral=True)
                return
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(webhook_url, session=session)
                for i in range(count):
                    await webhook.send(
                        content=message,
                        username=webhook_name,
                        avatar_url=webhook_avatar
                    )
                    await asyncio.sleep(delay)
                await interaction.followup.send(f"Sent {count} messages via webhook.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)
            return

class WebhookRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="webhook_raid", description="Send messages via webhook (authorized users only)")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def webhook_raid(self, interaction: discord.Interaction):
        await rlog(self.bot, "webhook_raid", interaction.user, interaction.guild_id)
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
            return await interaction.response.send_message(view=view, ephemeral=True)
        # End of checks
        await interaction.response.send_modal(WebhookRaidModal())


async def setup(bot):
    await bot.add_cog(WebhookRaid(bot))