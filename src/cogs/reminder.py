# reminder.py cog
# This cog lets users set reminders for themselves.
# The system works as follows:
#   1. The user uses the /reminder command
#   2. The command opens a modal for the user to fill out
#   3. The user submits the modal
#   4. The bot sends an ephemeral message to inform the user that the reminder has been set
#   5. The bot sends the reminder to the user's DMs at the specified time

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Modal, TextInput, Select, View, Button
import datetime

from utils.access_manager import AccessManager
from utils.raid_config import SERVER_INVITE
access = AccessManager()
reminders = {}

class ReminderModal(Modal):
    def __init__(self, bot):
        super().__init__(title="Set a Reminder")
        self.bot = bot
        self.reminder_input = TextInput(
            label="Reminder",
            placeholder="What do you need to be reminded of?",
            required=True,
            style=discord.TextStyle.paragraph
        )
        self.time_input = TextInput(
            label="Time (HH:MM)",
            placeholder="Enter time in 24-hour format (e.g., 14:30)",
            required=True
        )
        self.timezone_select = Select(
            placeholder="Select a timezone",
            options = []
        )
        self.add_item(self.reminder_input)
        self.add_item(self.time_input)
        self.add_item(self.timezone_select)

    async def on_submit(self, interaction: discord.Interaction):
        reminder_text = self.reminder_input.value
        time_str = self.time_input.value
        user_time_zone = self.timezone_select.values[0]
        # Dynamically determine the bot's host timezone
        bot_time_zone = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
        user = interaction.user
        try:
            # convert time input to the bot's time zone
            time_obj = datetime.datetime.strptime(time_str, "%H:%M").time()
            now = datetime.datetime.now(bot_time_zone)
            reminder_datetime = datetime.datetime.combine(now.date(), time_obj, bot_time_zone)
            if reminder_datetime < now:
                reminder_datetime += datetime.timedelta(days=1)
            # store the reminder
            if user.id not in reminders:
                reminders[user.id] = []
            reminders[user.id].append({
                "text": reminder_text,
                "time": reminder_datetime,
                "timezone": user_time_zone
            })
            # send confirmation
            confirmation_embed = discord.Embed(
                title="Reminder Set",
                description=f"Reminder set for {reminder_datetime.strftime('%H:%M')} {user_time_zone}: {reminder_text}",
                color=discord.Color.green()
            )
            confirmation_embed.set_footer(text="Lucid Raiding™ | All rights reserved")
            await interaction.response.send_message(embed=confirmation_embed, ephemeral=True)
        except ValueError:
            # handle invalid time format
            invalid_time_embed = discord.Embed(
                title="Invalid Time Format",
                description="Please enter the time in 24-hour format (e.g., 14:30).",
                color=discord.Color.red()
            )
            invalid_time_embed.set_footer(text="Lucid Raiding™ | All rights reserved")
            await interaction.response.send_message(embed=invalid_time_embed, ephemeral=True)
            return
        except Exception as e:
            # handle other errors
            error_embed = discord.Embed(
                title="Error",
                description=f"An error occurred while setting the reminder:\n```\n{e}\n```"
            )
            error_embed.set_footer(text="Lucid Raiding™ | All rights reserved")
            await interaction.response.send_message(embed=error_embed, ephemeral=True)
            return

class Reminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="reminder", description="Set a reminder for yourself.")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def reminder(self, interaction: discord.Interaction):
        # Guard check
        guard = await access.guard(interaction, {"action": "reminder", "cooldown_seconds": 60})
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
        modal = ReminderModal(self.bot)
        await interaction.response.send_modal(modal)

    @tasks.loop(minutes=1)
    async def check_reminders(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        for user_id, user_reminders in list(reminders.items()):
            for reminder in user_reminders[:]:
                if reminder["time"] <= now:
                    user = self.bot.get_user(user_id)
                    if user:
                        try:
                            reminder_embed = discord.Embed(
                                title="Reminder",
                                description=f"⏰️ **Reminder:**\n{reminder['text']}",
                                color=discord.Color.blue()
                            )
                            await user.send(embed=reminder_embed)
                        except discord.Forbidden:
                            print(f"[reminder] Could not send reminder to user {user_id} (DMs closed).")
                        except Exception as e:
                            print(f"[reminder] Error sending reminder to user {user_id}: {e}")
                    user_reminders.remove(reminder)
            if not user_reminders:
                del reminders[user_id]


async def setup(bot):
    await bot.add_cog(Reminder(bot))