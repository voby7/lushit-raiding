# request_raid.py cog
# Adds a command to request a raid
# Works is the following order:
# 1. User runs /request_raid
# 2. Opens a modal to enter the server invite link, whether or not external apps are enabled, and an optional message to include in the request
# 3. Bot sends the request to the raid request channel and pings the raid role
# 4. Bot sends an ephemeral message to the user confirming the request was sent

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput

from utils.raid_config import REQUEST_CHANNEL, RAID_ROLE, MAIN_GUILD, SERVER_INVITE
from utils.access_manager import AccessManager
access = AccessManager()

class RequestRaidModal(Modal, title="Request a Raid"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
    invite_link = TextInput(label="Server Invite Link", placeholder="https://discord.gg/...", required=True)
    message = TextInput(label="Message (Optional)", placeholder="Enter any additional information here", style=discord.TextStyle.paragraph, required=False)

    async def on_submit(self, interaction: discord.Interaction):
        # Using response.defer() but checking if it's already responded
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        invite_link = self.invite_link.value
        message = self.message.value if self.message.value else "No additional information provided."

        main_guild = self.bot.get_guild(MAIN_GUILD)
        request_channel = main_guild.get_channel(REQUEST_CHANNEL)
        if not request_channel:
            await interaction.followup.send("Error: Request channel not found.", ephemeral=True)
            return
        
        view = discord.ui.LayoutView()
        container = discord.ui.Container(
            discord.ui.TextDisplay(
                content="# ʀᴀɪᴅ ʀᴇǫᴜᴇsᴛ"
            ),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay(
                content=f"<@&{RAID_ROLE}>"
            ),
            discord.ui.TextDisplay(
                content=f"**Server Invite Link:**\n{invite_link}"
            ),
            discord.ui.TextDisplay(
                content=f"**Additional Information:**\n{message}"
            ),
            discord.ui.TextDisplay(
                content=f"-# Requested by {interaction.user.mention}"
            ),
            accent_colour=discord.Color.blue()
        )
        view.add_item(container)
        await request_channel.send(view=view)
        await interaction.followup.send("Your raid request has been sent successfully!", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        if not interaction.response.is_done():
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)
        else:
            await interaction.followup.send(f"An error occurred: {error}", ephemeral=True)

class RequestRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="request_raid", description="Request a raid")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def request_raid(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # Guard check
        guard = await access.guard(interaction, {"action": "request_raid", "cooldown_seconds": 60})
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
        # End of checks
        
        try:
            await interaction.followup.send(RequestRaidModal(self.bot))
        except Exception as e:
            # Interaction might have expired or modal couldn't be sent
            await interaction.followup.send(f"Could not open modal: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RequestRaid(bot))
