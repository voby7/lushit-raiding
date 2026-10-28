import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput
import random
import aiohttp
import os
import geoip2.database

from utils.access_manager import AccessManager

access = AccessManager()

# ===================================
# IP LOOKUP MODAL
# ===================================

class IPLookupModal(Modal, title="IP Lookup"):
    ip = TextInput(label="IP Address", placeholder="Example: 8.8.8.8", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        ip_addr = self.ip.value
        
        # MaxMind GeoLite2 lookup
        db_path = "GeoLite2-City.mmdb"
        city_data = {}
        if os.path.exists(db_path):
            try:
                with geoip2.database.Reader(db_path) as reader:
                    response = reader.city(ip_addr)
                    city_data = {
                        "city": response.city.name,
                        "region": response.subdivisions.most_specific.name,
                        "country": response.country.name,
                        "loc": f"{response.location.latitude}, {response.location.longitude}",
                        "postal": response.postal.code,
                        "timezone": response.location.time_zone
                    }
            except Exception as e:
                print(f"MaxMind Error: {e}")

        # ip-api.com lookup for VPN/Proxy
        vpn_data = {}
        async with aiohttp.ClientSession() as session:
            try:
                # ip-api.com pro features or specific fields
                # fields=66846719 includes proxy, vpn, etc.
                url = f"http://ip-api.com/json/{ip_addr}?fields=status,message,country,regionName,city,zip,lat,lon,timezone,isp,org,as,proxy,vpn,hosting"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        vpn_data = await resp.json()
            except Exception as e:
                print(f"IP-API Error: {e}")
        
        # Merge data preferring MaxMind for location if available
        city = city_data.get("city") or vpn_data.get("city", "N/A")
        region = city_data.get("region") or vpn_data.get("regionName", "N/A")
        country = city_data.get("country") or vpn_data.get("country", "N/A")
        loc = city_data.get("loc") or (f"{vpn_data.get('lat')}, {vpn_data.get('lon')}" if vpn_data.get("lat") else "N/A")

        # Security fields
        is_vpn = "Yes" if vpn_data.get("vpn") else "No"
        is_proxy = "Yes" if vpn_data.get("proxy") else "No"
        is_hosting = "Yes" if vpn_data.get("hosting") else "No"
        
        view = discord.ui.LayoutView()
        container = discord.ui.Container(
            discord.ui.TextDisplay(
                content=f"# IP Lookup: {ip_addr}"
            ),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay(
                content=f"## __Location Details:__"
            ),
            discord.ui.TextDisplay(
                content=f"**City:**\n-# {city}\n**Region:**\n-# {region}\n**Country:**\n-# {country}\n**Location:**\n-# {loc}\n**ISP:**\n-# {vpn_data.get('isp', 'N/A')}\n**Organization:**\n-# {vpn_data.get('org', 'N/A')}"
            ),
            discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small),
            discord.ui.TextDisplay(
                content="## __Security Details:__"
            ),
            discord.ui.TextDisplay(
                content=f"**VPN:**\n-# {is_vpn}\n**Proxy:**\n-# {is_proxy}\n**Hosting/DC:**\n-# {is_hosting}\n**Timezone:**\n-# {city_data.get('timezone') or vpn_data.get('timezone', 'N/A')}"
            )
        )
        view.add_item(container)
        await interaction.followup.send(view=view, ephemeral=True)

# ===================================
# UNIT CONVERTER LOGIC
# ===================================

def convert_units(category: str, value: float, from_unit: str, to_unit: str):
    category = category.lower()

    # Distance (meters as base)
    if category == "distance":
        factors = {
            "m": 1,
            "km": 1000,
            "ft": 0.3048,
            "mi": 1609.34,
            "cm": 0.01,
        }

    # Weight (grams as base)
    elif category == "weight":
        factors = {
            "g": 1,
            "kg": 1000,
            "lb": 453.592,
            "oz": 28.3495,
        }

    # Time (seconds as base)
    elif category == "time":
        factors = {
            "sec": 1,
            "min": 60,
            "hr": 3600,
            "day": 86400,
        }

    # Temperature (special case)
    elif category == "temperature":
        if from_unit == "C" and to_unit == "F":
            return value * 9/5 + 32
        if from_unit == "F" and to_unit == "C":
            return (value - 32) * 5/9
        if from_unit == "C" and to_unit == "K":
            return value + 273.15
        if from_unit == "K" and to_unit == "C":
            return value - 273.15
        if from_unit == "F" and to_unit == "K":
            return (value - 32) * 5/9 + 273.15
        if from_unit == "K" and to_unit == "F":
            return (value - 273.15) * 9/5 + 32
        return None

    else:
        return None

    # Standard conversion
    if from_unit not in factors or to_unit not in factors:
        return None

    base_value = value * factors[from_unit]
    return base_value / factors[to_unit]


# ===================================
# UNIT CONVERTER MODAL
# ===================================

class ConvertModal(Modal, title="Unit Converter"):
    category = TextInput(label="Category (distance/weight/temperature/time)")
    value = TextInput(label="Value", placeholder="Example: 10")
    from_unit = TextInput(label="From Unit", placeholder="Example: km")
    to_unit = TextInput(label="To Unit", placeholder="Example: m")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            num = float(self.value.value)
        except ValueError:
            await interaction.response.send_message("Invalid number.", ephemeral=True)
            return

        result = convert_units(
            self.category.value,
            num,
            self.from_unit.value,
            self.to_unit.value
        )

        if result is None:
            await interaction.response.send_message("Invalid conversion.", ephemeral=True)
            return

        embed = discord.Embed(
            title="Unit Conversion",
            description=f"**{num} {self.from_unit.value} → {result} {self.to_unit.value}**"
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


# ===================================
# CALCULATOR VIEW
# ===================================

class CalculatorView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.expression = ""

        # Row 0
        self.add_item(self.make_button("7", row=0))
        self.add_item(self.make_button("8", row=0))
        self.add_item(self.make_button("9", row=0))
        self.add_item(self.make_button("÷", row=0, custom_id="/", style=discord.ButtonStyle.primary))

        # Row 1
        self.add_item(self.make_button("4", row=1))
        self.add_item(self.make_button("5", row=1))
        self.add_item(self.make_button("6", row=1))
        self.add_item(self.make_button("×", row=1, custom_id="*", style=discord.ButtonStyle.primary))

        # Row 2
        self.add_item(self.make_button("1", row=2))
        self.add_item(self.make_button("2", row=2))
        self.add_item(self.make_button("3", row=2))
        self.add_item(self.make_button("−", row=2, custom_id="-", style=discord.ButtonStyle.primary))

        # Row 3
        self.add_item(self.make_button("0", row=3))
        self.add_item(self.make_button("C", row=3, custom_id="clear", style=discord.ButtonStyle.danger))
        self.add_item(self.make_button("=", row=3, custom_id="equals", style=discord.ButtonStyle.success))
        self.add_item(self.make_button("+", row=3, style=discord.ButtonStyle.primary))

    def make_button(self, label, *, custom_id=None, style=discord.ButtonStyle.secondary, row=0):
        return discord.ui.Button(
            label=label,
            style=style,
            custom_id=custom_id or label,
            row=row
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        cid = interaction.data.get("custom_id")
        if not cid:
            return False

        if cid == "clear":
            self.expression = ""
        elif cid == "equals":
            try:
                # Basic safety check (though this is just eval)
                # For production, use a proper parser
                self.expression = str(eval(self.expression))
            except Exception:
                self.expression = "Error"
        else:
            self.expression += cid

        await self.update_display(interaction)
        return True

    async def on_timeout(self):
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = True

    async def update_display(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Calculator",
            description=f"```\n{self.expression or '0'}\n```"
        )
        await interaction.response.edit_message(embed=embed, view=self)


# ===================================
# MAIN COG
# ===================================

class FunTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -------------------------------
    # /calculator
    # -------------------------------
    @app_commands.command(name="calculator", description="Open an interactive calculator.")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def calculator(self, interaction: discord.Interaction):
        # Guard check
        guard = await access.guard(interaction, {"action": "calculator", "cooldown_seconds": 60})
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
        # End of checks

        view = CalculatorView()
        embed = discord.Embed(title="Calculator", description="```\n0\n```")

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # -------------------------------
    # /8ball
    # -------------------------------
    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question.")
    @app_commands.describe(question="What do you want to ask the 8-ball?")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def eightball(self, interaction: discord.Interaction, question: str):
        # Guard check
        guard = await access.guard(interaction, {"action": "8ball", "cooldown_seconds": 60})
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

        responses = [
            "It is certain.",
            "Without a doubt.",
            "You may rely on it.",
            "Most likely.",
            "Outlook good.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Don't count on it.",
            "My reply is no.",
            "Very doubtful."
        ]

        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            description=f"**Question:** {question}\n**Answer:** {random.choice(responses)}"
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # -------------------------------
    # /convert
    # -------------------------------
    @app_commands.command(name="convert", description="Convert between units.")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def convert(self, interaction: discord.Interaction):
        # Guard check
        guard = await access.guard(interaction, {"action": "convert", "cooldown_seconds": 60})
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
        # End of checks

        await interaction.response.send_modal(ConvertModal())

    # -------------------------------
    # /iplookup
    # -------------------------------
    @app_commands.command(name="iplookup", description="Detailed IP information lookup.")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def iplookup(self, interaction: discord.Interaction):
        # Guard check
        guard = await access.guard(interaction, {"action": "iplookup", "cooldown_seconds": 60})
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
        # End of checks

        await interaction.response.send_modal(IPLookupModal())

    # -------------------------------
    # /permcheck
    # -------------------------------
    @app_commands.command(name="permcheck", description="Check if the bot can raid via interactions in this channel.")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def permcheck(self, interaction: discord.Interaction):
        # Guard check
        guard = await access.guard(interaction, {"action": "permcheck", "cooldown_seconds": 5})
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

        # Handle DM context
        if not interaction.guild or not interaction.channel:
            return await interaction.response.send_message("✅ This is a DM. You have full control over interactions here.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        
        # Check permissions in server channel
        permissions = interaction.channel.permissions_for(interaction.guild.me)
        
        has_send = permissions.send_messages
        has_external = permissions.use_external_emojis
        
        status = "✅️" if (has_send and has_external) else "⚠️"
        message = f"{status} **Raid Potential Analysis:**\n"
        message += f"- Send Messages: {'✅' if has_send else '❌'}\n"
        message += f"- External Interactions: {'✅' if has_external else '❌'}\n\n"
        
        if has_send and has_external:
            message += "This channel is highly vulnerable to interaction-based raids."
        elif has_send:
            message += "Raid is possible, but external app elements might be restricted."
        else:
            message += "Channel is well-protected against standard raiding."

        await interaction.followup.send(message, ephemeral=True)


async def setup(bot):
    await bot.add_cog(FunTools(bot))
