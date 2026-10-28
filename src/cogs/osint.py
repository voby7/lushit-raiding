# osint.py cog
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput
import asyncio
import os
from utils.access_manager import AccessManager
from utils.raid_logger import rlog
from utils.raid_config import SERVER_INVITE

access = AccessManager()

debug_mode = os.getenv("DEBUG_MODE")

class OSINTModal(Modal, title="OSINT Lookup (Sherlock)"):
    username = TextInput(
        label="Username to search",
        placeholder="Enter username (e.g. johndoe)",
        min_length=1,
        max_length=50,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Starting Sherlock search for `{self.username.value}`. This may take a minute... Results will be sent to your DMs.", ephemeral=True)
        
        target = self.username.value
        
        try:
            # Run sherlock as a subprocess
            output_file = f"{target}.txt"
            process = await asyncio.create_subprocess_exec(
                "sherlock", target, "--timeout", "1", "--output", output_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if os.path.exists(output_file):
                with open(output_file, "rb") as f:
                    discord_file = discord.File(f, filename=f"sherlock_{target}.txt")
                    try:
                        await interaction.user.send(f"Sherlock search results for `{target}`:", file=discord_file)
                        await interaction.followup.send("Results sent to your DMs.", ephemeral=True)
                    except discord.Forbidden:
                        await interaction.followup.send("Could not send DM. Please enable DMs from server members.", ephemeral=True)
                os.remove(output_file)
            else:
                await interaction.followup.send(f"No results found or Sherlock failed for `{target}`.", ephemeral=True)
                
        except Exception as e:
            await interaction.followup.send(f"Error running Sherlock: {e}", ephemeral=True)
            if debug_mode == "True":
                print("Sherlock Error:")
                print(f"  Lookup failed for {target}")
                print(f"  Requested by: {interaction.user}")
                print(f"  Error: {e}")

# ====================================
# COMMANDS
# ====================================
class OSINTCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="osint", description="Perform a Sherlock username lookup")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def osint(self, interaction: discord.Interaction):
        await rlog(self.bot, "osint", interaction.user, interaction.guild_id)
        # Guard check
        guard = await access.guard(interaction, {"action": "osint", "cooldown_seconds": 60})
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
        # End of checks

        await interaction.response.send_modal(OSINTModal())

async def setup(bot):
    await bot.add_cog(OSINTCog(bot))
