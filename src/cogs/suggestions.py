# suggestions.py cog
# This cog lets users submit suggestions to the bot developers.
# The system works as follows:
#   1. The user uses the /suggest command
#   2. The command opens a modal for the user to fill out
#   3. The user submits the modal
#   4. The bot sends it to a private channel as an embed with the user's profile picture and username in the footer
#   5. The bot sends a confirmation message to the user to inform them that their suggestion was sent successfully

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput

from utils.raid_config import SERVER_INVITE
from utils.access_manager import AccessManager
access = AccessManager()

suggestion_channel_id = 1463889104113762364


class SuggestionModal(Modal):
    def __init__(self, bot):
        super().__init__(title="Submit a Suggestion")
        self.bot = bot

        self.suggestion_input = TextInput(
            label="Your Suggestion",
            placeholder="Describe your idea or suggestion here...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )

        self.add_item(self.suggestion_input)

    async def on_submit(self, interaction: discord.Interaction):
        suggestion_text = self.suggestion_input.value
        user = interaction.user

        # Build the embed
        embed = discord.Embed(
            title="New Suggestion",
            description=suggestion_text,
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"{user.name}", icon_url=user.display_avatar.url)

        # Send to the private suggestion channel
        channel = self.bot.get_channel(suggestion_channel_id)
        if channel:
            await channel.send(embed=embed)

        # Confirmation message to the user
        await interaction.response.send_message(
            "Thank you! Your suggestion has been submitted successfully.",
            ephemeral=True
        )


class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="suggest", description="Submit a suggestion to the bot developers.")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def suggest(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # Guard check
        guard = await access.guard(interaction, {"action": "suggest", "cooldown_seconds": 180})
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
        modal = SuggestionModal(self.bot)
        await interaction.followup.send(modal)


async def setup(bot):
    await bot.add_cog(Suggestions(bot))