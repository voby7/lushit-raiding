import discord
from discord import app_commands
from discord.ext import commands
import os
from utils.access_manager import AccessManager

access = AccessManager()

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command: discord.app_commands.Command):
        access.increment_command_count()

    @app_commands.command(name="post_bot_link", description="Post the bots authorization link (owner only)")
    async def post_bot_link(self, interaction: discord.Interaction):
        if not access.is_owner(interaction.user.id):
            await interaction.response.send_message("Owner only.", ephemeral=True)
            return
        channel_link = "https://discord.com/channels/1482032314014896220/1482162086485299242"
        link = f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}"
        message = f"# ʟᴜᴄɪᴅ ʀᴀɪᴅɪɴɢ™ ʀᴀɪᴅʙᴏᴛ\nғᴏʀ ᴀᴄᴄᴇss ᴛᴏ ᴛʜᴇ ʀᴀɪᴅʙᴏᴛ ᴘʟᴇᴀsᴇ ᴀᴅᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ʏᴏᴜʀ ᴀᴘᴘs ᴀɴᴅ ᴛʜᴇɴ ᴠᴇʀɪғʏ ᴜsɪɴɢ ᴛʜᴇ **ᴠᴀᴜʟᴛᴄᴏʀᴅ ʟɪɴᴋ** ɪɴ {channel_link}\n> ɪғ ʏᴏᴜ ᴀʀᴇ ᴜɴsᴜʀᴇ ɪғ ʏᴏᴜ ʜᴀᴠᴇ ᴀᴄᴄᴇss ᴜsᴇ ⁨⁨`/authcheck`⁩⁩ ᴀɴᴅ ɪᴛ ᴡɪʟʟ ᴛᴇʟʟ ʏᴏᴜ ɪғ ʏᴏᴜ ᴀʀᴇ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ\n**ᴜsᴇ ᴛʜɪs ʟɪɴᴋ ᴛᴏ ᴀᴜᴛʜᴏʀɪᴢᴇ ᴛʜᴇ ʙᴏᴛ:**\n{link}"
        view = discord.ui.LayoutView()
        container = discord.ui.Container(
            discord.ui.TextDisplay(
                content=message
            )
        )
        view.add_item(container)
        try:
            await interaction.channel.send(view=view)
            await interaction.response.send_message("done", ephemeral=True)
        except Exception:
            await interaction.response.send_message("you cannot do that here dumbass", ephemeral=True)

    # @app_commands.command(name="authorize", description="Authorize a user to use the bot (owner only)")
    # @app_commands.describe(user="User to authorize")
    # async def authorize(self, interaction: discord.Interaction, user: discord.User):
    #     if not access.is_owner(interaction.user.id):
    #         await interaction.response.send_message("Owner only.", ephemeral=True)
    #         return
    #     access.allow_user(user.id, actor={"id": interaction.user.id, "tag": f"{interaction.user.name}#{interaction.user.discriminator}"})
    #     await interaction.response.send_message(f"Authorized {user.mention}.", ephemeral=True)

    @app_commands.command(name="block", description="Block a user from using the bot (owner only)")
    @app_commands.describe(user="User to block")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def block(self, interaction: discord.Interaction, user: discord.User):
        if not access.is_owner(interaction.user.id):
            await interaction.response.send_message("Owner only.", ephemeral=True)
            return
        access.block_user(user.id, actor={"id": interaction.user.id, "tag": f"{interaction.user.name}#{interaction.user.discriminator}"})
        await interaction.response.send_message(f"Blocked {user.mention}.", ephemeral=True)

    @app_commands.command(name="unblock", description="Unblock a user (owner only)")
    @app_commands.describe(user="User to unblock")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def unblock(self, interaction: discord.Interaction, user: discord.User):
        if not access.is_owner(interaction.user.id):
            await interaction.response.send_message("Owner only.", ephemeral=True)
            return
        access.unblock_user(user.id, actor={"id": interaction.user.id, "tag": f"{interaction.user.name}#{interaction.user.discriminator}"})
        await interaction.response.send_message(f"Unblocked {user.mention}.", ephemeral=True)

    @app_commands.command(name="lock", description="Enable or disable global lock (owner only)")
    @app_commands.describe(state="on or off")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def lock(self, interaction: discord.Interaction, state: str):
        if not access.is_owner(interaction.user.id):
            await interaction.response.send_message("Owner only.", ephemeral=True)
            return
        val = state.lower() == "on"
        access.set_global_lock(val, actor={"id": interaction.user.id, "tag": f"{interaction.user.name}#{interaction.user.discriminator}"})
        await interaction.response.send_message(f"Global lock set to {'ON' if val else 'OFF'}.", ephemeral=True)

    @app_commands.command(name="status", description="Owner-only: show authorization and lock status")
    @app_commands.describe(ephemeral="Whether to send the response privately (default: True)")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def status(self, interaction: discord.Interaction, ephemeral: bool = False):
        allowed_count = len(access.list_authorized())
        blocked_count = len(access.list_blocked())
        locked = "ON" if access.state.get("global_locked") else "OFF"
        version = os.environ.get("BOT_VERSION")

        embed = discord.Embed(
            title="🔒 Bot Status",
            color=discord.Color.red() if locked == "ON" else discord.Color.green()
        )
        embed.add_field(name="Owner", value=f"<@{access.state.get('owner_id')}>", inline=False)
        embed.add_field(name="Global Lock", value=locked, inline=True)
        embed.add_field(name="Authorized Users", value=str(allowed_count), inline=True)
        embed.add_field(name="Blocked Users", value=str(blocked_count), inline=True)
        embed.add_field(name="Uptime", value=access.get_uptime(), inline=False)
        embed.add_field(name="Commands Run", value=str(access.get_command_count()), inline=True)
        embed.add_field(name="Version", value=f"{version}", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

    @app_commands.command(name="authcheck", description="Check if you are authorized")
    async def authcheck(self, interaction: discord.Interaction):
        guard = await access.guard(interaction, {"action": "authcheck", "cooldown_seconds": 2})
        if not guard.get("ok"):
            reason = str(guard.get("reason", "unknown"))
            msg = {
                "not_authorized": "You are not authorized to use this bot.\nPlease join the server and verify to get access.\nhttps://discord.gg/PPgrmNzukN",
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
        await interaction.response.send_message(f"Hello {interaction.user.mention} — you are authorized.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
