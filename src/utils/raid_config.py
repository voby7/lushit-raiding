# raid_config.py
import discord
from datetime import datetime
import os

# This is the logo that will be displayed in the embeds sent by the bot
LOGO_URL = None

# This is the invite that will be used in the raid commands
SERVER_INVITE = "https://discord.gg/JuxgqYESUm"

# This is the role users must have to use the bot
VERIFIED_ROLE = 1482161707316019432

# This is the server ID of the main guild where the bot will send the raid requests and raid logs
MAIN_GUILD = 1482032314014896220

# This is the channel where raid requests will be sent
REQUEST_CHANNEL = 1482162117556568200

# This is the channel where raid logs will be sent
RAID_LOG_CHANNEL = 1482164557928468632
MESSAGE_LOG_CHANNEL = 1482164557928468632

# This is the role that will be pinged when a raid request is sent
RAID_ROLE = 1482161714907713641

# The message that will be sent during a /raid
# Pulled from templates/template1.txt
RAID_MESSAGE = (open("src/templates/template1.txt", "r").read())

# Maximum number of messages allowed per raid
MAX_MESSAGES = 5 # This number cannot go any higher than 5 due to the Discord external apps policy

# Cooldown in seconds between raids per guild
COOLDOWN_SECONDS = 5

# Raid embed config
VIEW_CONFIG = {
    "title": "SERVER RAIDED BY Lucid Raiding™ 🔥",
    "description": "You've been raided by Lucid Raiding™!\nThis server has been compromised.",
    "color": discord.Color.red(),
    "fields": [
        {"name": "Raided By", "value": "Lucid Raiding™"}
    ],
    "footer": "- Lucid Raiding™ | {timestamp}"
}

def get_raid_view():
    view = discord.ui.LayoutView()
    container = discord.ui.Container(
        discord.ui.TextDisplay(
            content=f"## {VIEW_CONFIG['title']}"
        ),
        discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
        discord.ui.TextDisplay(
            content=str(VIEW_CONFIG["description"])
        ),
        accent_colour=discord.Color.red()
    )

    # Add static fields
    for field in VIEW_CONFIG["fields"]:
        container.add_item(discord.ui.TextDisplay(content=f"**{field['name']}:** {field['value']}"))

    # Footer with dynamic timestamp
    timestamp = datetime.now()
    timestamp = f"<t:{int(timestamp.timestamp())}:F>"
    footer = VIEW_CONFIG["footer"].format(timestamp=timestamp)
    container.add_item(discord.ui.TextDisplay(content=f"-# {footer}"))

    view.add_item(container)
    return view
