import discord
from discord import app_commands
from discord.ext import commands
import utils.db as db
import time
import re
import datetime
from typing import Literal

def parse_duration(duration_str): # convert 1m, 1h, 1d, etc to seconds and then to a timedelta
	pattern = r"(\d+)([mh]?)"
	match = re.search(pattern, duration_str)
	if match:
		num, unit = match.groups()
		if unit == 's':
			factor = 1
		elif unit == 'm':
			factor = 60
		elif unit == 'h':
			factor = 3600
		elif unit == 'd':
			factor = 86400
		else:
			factor = 1
		
		total_seconds = float(num) * factor
		
		return datetime.timedelta(seconds=total_seconds)
	else:
		raise ValueError(f"Invalid duration format: {duration_str}")

class moderation(commands.Cog):
	@app_commands.command()
	@app_commands.describe(victim="Member to sanction")
	@app_commands.describe(severity="Type of sanction")
	@app_commands.describe(duration="Time of mute (eg: 1s for 1 second, 1m for 1 minute, 1h for 1 hour, 1d for 1 day.)")
	@app_commands.describe(reason="Reason of mute")
	@app_commands.rename(victim='member')
	async def mute(self,interaction: discord.Interaction, victim: discord.Member, severity: Literal['S2', 'N/A'], duration: str, reason: str):
		try:
			guild_id = interaction.guild.id
			user_id = victim.id
			moderator_id = interaction.user.id
			duration_delta = parse_duration(duration)
			await victim.timeout(duration_delta, reason=f"{reason} - {interaction.user.name}", )
			await interaction.response.send_message(f"Moderation `{db.insert_moderation(guild_id=guild_id, user_id=user_id, moderator_id=moderator_id, moderation_type=reason, severity=severity, duration=duration, time=str(time.time()))}`: Muted <@{user_id}> for {duration}: **{severity}. {reason}**")
		except Exception as e:
			await interaction.response.send_message("Unhandled exception caught:\n```\n{e}\n```", ephemeral=True)

async def setup(client):
	await client.add_cog(moderation(client))