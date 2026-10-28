import discord
from discord import app_commands
from discord.ext import commands

from utils.raid_logger import rlog
from utils.raid_config import LOGO_URL, MAIN_GUILD, SERVER_INVITE
from utils.access_manager import AccessManager
access = AccessManager()

allowed_mentions = discord.AllowedMentions(everyone=True, roles=True, users=True)

class Advertisement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="advertise", description="Advertise our server!")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def advertise(self, interaction: discord.Interaction):
        await rlog(self.bot, "advertise", interaction.user, interaction.guild_id)
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
        # Send the message anonymously
        await interaction.response.send_message(f"{SERVER_INVITE}", ephemeral=True)
        # Send the actual public ad as a non ephemeral message but replying to the ephemeral message to ensure it is anonymous
        view = discord.ui.LayoutView()
        container = discord.ui.Container(
            discord.ui.TextDisplay(
                content="# Lucid Rxiding™"
            ),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay(
                content="Are you ready to take your rxids to the next level?\nAt Lucid Rxiding™, we specialize in providing top-tier rxid services to help you dominate the competition."
            ),
            discord.ui.TextDisplay(
                content="**What we offer:**\n> `✅️` Fast and reliable bots\n> `✅️` Friendly and helpful staff\n> `✅️` Customizable rxid options\n> `✅️` An inclusive and welcoming community\n> `✅️` Regular updates and improvements\n> `✅️` An open-source s3lfbot"
            ),
            discord.ui.TextDisplay(
                content="We are committed to providing the best possible experience for our members, and we are always looking for ways to improve. Join us today and see the difference for yourself!"
            ),
            discord.ui.TextDisplay(
                content="-# “Your rxids, our precision” — Lucid Rxiding™"
            ),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay(
                content="-# @everyone @here"
            ),
            discord.ui.ActionRow(
                discord.ui.Button(
                    label="Join Now",
                    url=f"{SERVER_INVITE}",
                    style=discord.ButtonStyle.link
                )
            )
        )
        view.add_item(container)
        # Send the embed as a reply to the ephemeral message
        await interaction.followup.send(view=view, allowed_mentions=allowed_mentions)

async def setup(bot):
    await bot.add_cog(Advertisement(bot))
