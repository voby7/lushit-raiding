# template_raid.py cog
# This cog is basically just the menu command but each button raids with a different template.
# Templates will be stored in the templates folder as template1.txt, template2.txt, etc. cus I am too lazy to make a proper database or use fancy file types and shit ngl.
# I will add on more templates in the future as I make new ones and I will go ahead and add extra buttons and just disable them if I don't have a template for them yet.
# The template that will be used will be determined by the button's custom_id by adding .txt to the end of the custom_id.
# - Nyxen

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
import asyncio
import os

from utils.raid_logger import rlog
from utils.raid_config import LOGO_URL, MAIN_GUILD, SERVER_INVITE
from utils.access_manager import AccessManager
access = AccessManager()

allowed_mentions = discord.AllowedMentions(everyone=True)

# ====================================
# VIEW AND BUTTONS
# ====================================
class TemplateRaidButtons1(discord.ui.ActionRow):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.raid_tasks = {}

        # Row 1 (buttons 1-5)
        self.add_item(discord.ui.Button(label="Raid 1", style=discord.ButtonStyle.primary, custom_id="template1"))
        self.add_item(discord.ui.Button(label="Raid 2", style=discord.ButtonStyle.primary, custom_id="template2"))
        self.add_item(discord.ui.Button(label="Raid 3", style=discord.ButtonStyle.primary, custom_id="template3"))
        self.add_item(discord.ui.Button(label="Raid 4", style=discord.ButtonStyle.primary, custom_id="template4"))
        self.add_item(discord.ui.Button(label="Raid 5", style=discord.ButtonStyle.primary, custom_id="template5"))

    # Button click handler
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        button = interaction.data.get("custom_id")
        if not button:
            return False
        template_file = f"src/templates/{button}.txt"
        # Check if the template file exists
        if not os.path.exists(template_file):
            return await interaction.response.send_message("This template does not exist yet.", ephemeral=True)
        # Read the template file
        with open(template_file, "r"):
            template = open(template_file, "r").read()
        await interaction.response.send_message("Raid burst triggered!", ephemeral=True)
        # Trigger the raid burst (5 messages per button click)
        for _ in range(5):
            try:
                await interaction.followup.send(template)
                await asyncio.sleep(0.5)
            except Exception as e:
                if e.code == 40060:
                    print("Error: Rate limit exceeded.")
                if e.code == 50013:
                    print("Error: Missing permissions.")
                else:
                    print(f"Error: {e}")


class TemplateRaidButtons2(discord.ui.ActionRow):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.raid_tasks = {}

        # Row 2 (buttons 6-10)
        self.add_item(discord.ui.Button(label="Raid 6", style=discord.ButtonStyle.primary, custom_id="template6"))
        self.add_item(discord.ui.Button(label="Raid 7", style=discord.ButtonStyle.primary, custom_id="template7"))
        self.add_item(discord.ui.Button(label="Raid 8", style=discord.ButtonStyle.primary, custom_id="template8"))
        self.add_item(discord.ui.Button(label="Raid 9", style=discord.ButtonStyle.primary, custom_id="template9"))
        self.add_item(discord.ui.Button(label="Raid 10", style=discord.ButtonStyle.primary, custom_id="template10"))

    # Button click handler
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        button = interaction.data.get("custom_id")
        if not button:
            return False
        template_file = f"src/templates/{button}.txt"
        # Check if the template file exists
        if not os.path.exists(template_file):
            return await interaction.response.send_message("This template does not exist yet.", ephemeral=True)
        # Read the template file
        with open(template_file, "r"):
            template = open(template_file, "r").read()
        await interaction.response.send_message("Raid burst triggered!", ephemeral=True)
        # Trigger the raid burst (5 messages per button click)
        for _ in range(5):
            try:
                await interaction.followup.send(template)
                await asyncio.sleep(0.5)
            except Exception as e:
                if e.code == 40060:
                    print("Error: Rate limit exceeded.")
                if e.code == 50013:
                    print("Error: Missing permissions.")
                else:
                    print(f"Error: {e}")

# ====================================
# COMMANDS
# ====================================
class TemplateRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.buttons_1 = TemplateRaidButtons1(bot)
        self.buttons_2 = TemplateRaidButtons2(bot)

    @app_commands.command(name="template_raid", description="Raid using templates.")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def template_raid(self, interaction: discord.Interaction):
        await rlog(self.bot, "template_raid", interaction.user, interaction.guild_id)
        # Guard check
        guard = await access.guard(interaction, {"action": "template_raid", "cooldown_seconds": 60})
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
        template_view = discord.ui.LayoutView()
        container = discord.ui.Container(
            discord.ui.TextDisplay(
                content="### Template Raid"
            ),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay(
                content="Use the buttons below to raid using different templates.\n**Templates:**\n**1.** Classic Raid\n**2.** Lag Raid 💥\n**3.** Femboy Raid\n**4.** Gay shit ig\n**5.** Ragebait 🤬\n**6.** Blinding 🫣\n**7.** Unused\n**8.** Unused\n**9.** Unused\n**10.** Unused"
            ),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
        )
        # Note:
        # you cannot add the buttons as a container or a view because you cannot add those inside of a container.
        container.add_item(self.buttons_1)
        container.add_item(self.buttons_2)
        template_view.add_item(container)
        await interaction.response.send_message(view=template_view, ephemeral=True, allowed_mentions=allowed_mentions)

async def setup(bot):
    await bot.add_cog(TemplateRaid(bot))
