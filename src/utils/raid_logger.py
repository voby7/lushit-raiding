# raid_logger.py
# This file handles sending raid log embeds to the raid log channel
# It will be imported in the cogs that need to send raid logs and then it will be called using the rlog(command, user, guild_id) function
# The command parameter is the command that was used to trigger the raid
# The user parameter is the user that triggered the command
# The guild_id parameter is the guild_id that it was triggered in (if it was used in a DM then it will be set to None)
# The function will handle building and sending the embed to the raid log channel

import discord
import colorama
from utils.raid_config import RAID_LOG_CHANNEL, MESSAGE_LOG_CHANNEL, MAIN_GUILD, LOGO_URL
from datetime import datetime

async def rlog(bot, command, user, guild_id):
    # Get the main guild
    main_guild = bot.get_guild(MAIN_GUILD)
    if not main_guild:
        print(colorama.Fore.RED + f"Error: Main guild not found. Guild ID: {MAIN_GUILD}" + colorama.Style.RESET_ALL)
        return
    # Get the log channel
    log_channel = main_guild.get_channel(RAID_LOG_CHANNEL)
    if not log_channel:
        print(colorama.Fore.RED + f"Error: Log channel not found. Channel ID: {RAID_LOG_CHANNEL}" + colorama.Style.RESET_ALL)
        return
    # Build the log message
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    guild_id = guild_id if guild_id else "unknown"
    view = discord.ui.LayoutView()
    container = discord.ui.Container(
        discord.ui.TextDisplay(
            content="## ʀᴀɪᴅ ʟᴏɢ"
        ),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
        discord.ui.TextDisplay(
            content=f"**Command:** {command}"
        ),
        discord.ui.TextDisplay(
            content=f"**User:** {user.name} (`{user.id}`)"
        ),
        discord.ui.TextDisplay(
            content=f"**Guild ID:** {guild_id}"
        ),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
        discord.ui.TextDisplay(
            content=f"-# Lucid Raiding™ | {timestamp}"
        )
    )
    view.add_item(container)
    # Send the log embed to the log channel in the main guild
    await log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())



# custom message logger
async def cmlog(bot, user, message):
    # Get the main guild
    main_guild = bot.get_guild(MAIN_GUILD)
    if not main_guild:
        print(colorama.Fore.RED + f"Error: Main guild not found. Guild ID: {MAIN_GUILD}" + colorama.Style.RESET_ALL)
        return
    # Get the log channel
    log_channel = main_guild.get_channel(MESSAGE_LOG_CHANNEL)
    if not log_channel:
        print(colorama.Fore.RED + f"Error: Log channel not found. Channel ID: {MESSAGE_LOG_CHANNEL}" + colorama.Style.RESET_ALL)
        return
    # Build the log message
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    view = discord.ui.LayoutView()
    container = discord.ui.Container(
        discord.ui.TextDisplay(
            content="## ᴄᴜsᴛᴏᴍ ᴍᴇssᴀɢᴇ ʟᴏɢ"
        ),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
        discord.ui.TextDisplay(
            content=f"**User:** {user.name} (`{user.id}`)"
        ),
        discord.ui.TextDisplay(
            content=f"**Message:**\n{message}"
        ),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
        discord.ui.TextDisplay(
            content=f"-# Lucid Raiding™ | {timestamp}"
        )
    )
    view.add_item(container)
    # Send the log embed to the log channel in the main guild
    await log_channel.send(view=view, allowed_mentions=discord.AllowedMentions.none())
