# interaction_raid.py cog
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
from utils.raid_config import RAID_MESSAGE, MAIN_GUILD, SERVER_INVITE
from utils.raid_logger import rlog
from utils.access_manager import AccessManager

access = AccessManager()

class InteractionRaidView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Store individual interaction objects to use their unique followup tokens
        self.interaction_webhooks = []

    @discord.ui.button(label="Add Token (0)", style=discord.ButtonStyle.primary, custom_id="add_token")
    async def add_token(self, interaction: discord.Interaction, button: discord.ui.Button):
        # We store the interaction object itself. 
        # Each interaction has a unique webhook/followup token valid for 15 minutes.
        self.interaction_webhooks.append(interaction)
        button.label = f"Add Token ({len(self.interaction_webhooks)})"
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Execute Raid", style=discord.ButtonStyle.danger, custom_id="execute_raid")
    async def execute_raid(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.interaction_webhooks:
            await interaction.response.send_message("Add at least one token first!", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        # Calculate messages based on tokens (5 per token)
        total_tokens = len(self.interaction_webhooks)
        messages_per_token = 5
        total_messages = total_tokens * messages_per_token

        await interaction.followup.send(f"Executing raid with {total_messages} messages across {total_tokens} tokens...", ephemeral=True)

        # Create tasks for parallel sending across all tokens
        tasks = []
        for webhook_interaction in self.interaction_webhooks:
            tasks.append(self._send_burst(webhook_interaction, messages_per_token))

        # Run all bursts in parallel
        await asyncio.gather(*tasks)

        self.interaction_webhooks = []
        # Update labels correctly by iterating and checking type
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                if child.custom_id == "add_token":
                    child.label = "Add Token (0)"

        await interaction.edit_original_response(view=self)

    async def _send_burst(self, interaction: discord.Interaction, count: int):
        for i in range(count):
            try:
                # Use the stored interaction's followup to send messages
                await interaction.followup.send(RAID_MESSAGE)
                await asyncio.sleep(random.uniform(0.5, 1.0))
            except Exception as e:
                print(f"Error in interaction raid burst: {e}")
                break

# ===================================
# COMMANDS
# ===================================
class InteractionRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="interaction_raid", description="Start an interaction raid")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def interaction_raid(self, interaction: discord.Interaction):
        await rlog(self.bot, "interaction_raid", interaction.user, interaction.guild_id)
        # Guard check
        guard = await access.guard(interaction, {"action": "interaction_raid", "cooldown_seconds": 60})
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

        embed = discord.Embed(
            title="Interaction Raid",
            description="Click 'Add Token' multiple times to collect unique interaction tokens, then 'Execute Raid'. Each token adds 5 messages to the raid burst.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, view=InteractionRaidView(), ephemeral=True)

async def setup(bot):
    await bot.add_cog(InteractionRaid(bot))
