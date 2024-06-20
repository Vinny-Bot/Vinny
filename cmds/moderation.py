import discord
from discord import app_commands
from discord.ext import commands
import utils.db as db
import time
import re
import datetime
from typing import Literal
from utils import utils

class moderation(commands.Cog):
	@app_commands.command()
	@app_commands.describe(victim="Member to sanction")
	@app_commands.describe(severity="Type of sanction")
	@app_commands.describe(duration="Time of mute (eg: 1s for 1 second, 1m for 1 minute, 1h for 1 hour, 1d for 1 day.)")
	@app_commands.describe(reason="Reason of mute")
	@app_commands.rename(victim='member')
	@app_commands.checks.has_permissions(moderate_members=True)
	async def mute(self,interaction: discord.Interaction, victim: discord.Member, severity: Literal['S2', 'N/A'], duration: str, reason: str):
		try:
			guild_id = interaction.guild.id
			user_id = victim.id
			moderator_id = interaction.user.id
			duration_delta = utils.parse_duration(duration)
			await victim.timeout(duration_delta, reason=f"{reason} - {interaction.user.name}", )
			await interaction.response.send_message(f"Moderation `{db.insert_moderation(guild_id=guild_id, user_id=user_id, moderator_id=moderator_id, moderation_type=reason, severity=severity, duration=duration, time=str(time.time()))}`: Muted <@{user_id}> for {duration}: **{severity}. {reason}**")
		except Exception as e:
			await interaction.response.send_message(f"Unhandled exception caught:\n```\n{e}\n```", ephemeral=True)

	@app_commands.command()
	@app_commands.describe(victim="Member to sanction")
	@app_commands.describe(severity="Type of sanction")
	@app_commands.describe(duration="Time of ban (eg: 1s for 1 second, 1m for 1 minute, 1h for 1 hour, 1d for 1 day.)")
	@app_commands.describe(reason="Reason of ban")
	@app_commands.describe(purge="Purge all messages within 7 days")
	@app_commands.rename(victim='member')
	@app_commands.checks.has_permissions(ban_members=True)
	async def ban(self,interaction: discord.Interaction, victim: discord.Member, severity: Literal['S3', 'S4'], duration: str, reason: str, purge: Literal['No', 'Yes']):
		try:
			guild_id = interaction.guild.id
			user_id = victim.id
			moderator_id = interaction.user.id
			await victim.ban(delete_message_days=7, reason=f"{reason} - {interaction.user.name}\nbanned for {duration}")
			if severity == 'S4':
				duration = 'inf'
			await interaction.response.send_message(f"Moderation `{db.insert_moderation(guild_id=guild_id, user_id=user_id, moderator_id=moderator_id, moderation_type=reason, severity=severity, duration=duration, time=str(time.time()))}`: Banned <@{user_id}> for **`{duration}`**: **{severity}. {reason}**")
		except Exception as e:
			await interaction.response.send_message(f"Unhandled exception caught:\n```\n{e}\n```", ephemeral=True)

	@app_commands.command()
	@app_commands.describe(victim="Member to sanction")
	@app_commands.describe(severity="Type of sanction")
	@app_commands.describe(reason="Reason of warn")
	@app_commands.rename(victim='member')
	@app_commands.checks.has_permissions(moderate_members=True)
	async def warn(self,interaction: discord.Interaction, victim: discord.Member, severity: Literal['S1', 'N/A'], reason: str):
		try:
			guild_id = interaction.guild.id
			user_id = victim.id
			moderator_id = interaction.user.id
			await interaction.response.send_message(f"Moderation `{db.insert_moderation(guild_id=guild_id, user_id=user_id, moderator_id=moderator_id, moderation_type=reason, severity=severity, duration=None, time=str(time.time()))}`: Warned <@{user_id}>: **{severity}. {reason}**")
			channel = await victim.create_dm()
			await channel.send(f"You have been warned for: **{reason}**")
		except Exception as e:
			await interaction.response.send_message(f"Unhandled exception caught:\n```\n{e}\n```", ephemeral=True)

async def setup(client):
	await client.add_cog(moderation(client))