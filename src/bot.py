# bot.py
# Main entry point for the Discord bot
# Loads cogs and sets up the bot client and then displays a legal disclaimer with an ascii art banner

import os
import sys
import threading
import logging
import colorama
import discord
import aiohttp
from discord.ext import commands
from dotenv import load_dotenv
from utils.loader import load_cogs

# Ensure src/ is on the path so sibling modules (web, utils) resolve correctly
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

load_dotenv()

PROXY_URL = "http://31.56.127.193:7684"
PROXY_AUTH = aiohttp.BasicAuth(login="xkrnzrun", password="966fx5n7k1y9")

TOKEN = os.environ.get("DISCORD_TOKEN")
BOT_OWNER_ID = os.environ.get("BOT_OWNER_ID")

if not TOKEN:
    raise SystemExit(f"{colorama.Fore.RED}Set DISCORD_TOKEN in environment{colorama.Style.RESET_ALL}")   

if not BOT_OWNER_ID:
    raise SystemExit(f"{colorama.Fore.RED}Set BOT_OWNER_ID in environment{colorama.Style.RESET_ALL}")

log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=log_level)
logger = logging.getLogger("bot")
# ---------------------------- #
# Logger levels:               #
# ---------------------------- #
# DEBUG         logger.debug() #
# INFO           logger.info() #
# WARNING     logger.warning() #
# ERROR         logger.error() #
# CRITICAL   logger.critical() #
# ---------------------------- #

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, proxy=PROXY_URL, proxy_auth=PROXY_AUTH)

def display_disclaimer():
    print(
        """
██╗     ██╗   ██╗ ██████╗██╗██████╗ 
██║     ██║   ██║██╔════╝██║██╔══██╗
██║     ██║   ██║██║     ██║██║  ██║
██║     ██║   ██║██║     ██║██║  ██║
███████╗╚██████╔╝╚██████╗██║██████╔╝
╚══════╝ ╚═════╝  ╚═════╝╚═╝╚═════╝ 
        """
    )
    print("")
    print("Lucid Raiding™ Official Raid Bot")
    print("")
    print("Designed by Nyxen (Owner/Founder of Lucid Raiding™)")
    print("")
    print(f"{colorama.Fore.RED}{colorama.Style.BRIGHT}IMPORTANT NOTICE:{colorama.Style.RESET_ALL}")
    print(f"{colorama.Fore.RED}This software is for educational purposes only. The original author is not responsible or liable for any misuse of this software. All actions and or activities related to the use of this software is solely the responsibility of the user.{colorama.Style.RESET_ALL}")
    print("")
    print(f"{colorama.Fore.LIGHTBLACK_EX}If you have any questions regarding the use of this software, please contact the original author.{colorama.Style.RESET_ALL}")
    print("")

async def set_status(bot):
    # Set the status to streaming on a random twitch channel that doesn't exist
    twitch_channel = "lucidraiding"
    await bot.change_presence(activity=discord.Streaming(name="Lucid Raiding™", url=f"https://www.twitch.tv/{twitch_channel}"))

@bot.event
async def on_ready():
    os.system("cls" if os.name == "nt" else "clear")
    print(f"{colorama.Fore.GREEN}Logged in as {bot.user} (ID: {bot.user.id}){colorama.Style.RESET_ALL}")
    await load_cogs(bot)
    await set_status(bot)
    try:
        bot.loop.create_task(bot.tree.sync())
        print(f"{colorama.Fore.YELLOW}Command synchronization initiated globally.{colorama.Style.RESET_ALL}")
    except Exception as e:
        print(f"{colorama.Fore.RED}Failed to sync commands: {e}{colorama.Style.RESET_ALL}")

    display_disclaimer()

def _start_oauth_server() -> None:
    """Start the aiohttp OAuth credential-capture server on port 5000."""
    try:
        import importlib
        web_mod = importlib.import_module("web")
        web_mod._run_webserver()
    except Exception as exc:
        print(f"{colorama.Fore.YELLOW}[web] OAuth server failed to start: {exc}{colorama.Style.RESET_ALL}")


if __name__ == "__main__":
    # oauth_thread = threading.Thread(target=_start_oauth_server, daemon=True, name="oauth-server")
    # oauth_thread.start()
    bot.run(TOKEN)
