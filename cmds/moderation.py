# pakmar - discord moderation bot
# Copyright (C) 2024 0vf
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import discord
from discord import app_commands
from discord.ext import commands
import utils.db as db
import time
import re
import datetime
from typing import Literal
from utils import utils
from utils import embeds

class moderation(commands.Cog):
	def __init__(self, bot: commands.Bot) -> None:
		self.bot = bot

	async def log_embed(self,victim: discord.Member, severity: str, duration: str, reason: str, moderator: discord.Member, moderation_id: str, moderation_type: str, guild: discord.Guild):
		embed = discord.Embed(title=f"Moderation `{moderation_id}` - {moderation_type}", color=16711680)
		embed.add_field(name="Moderated member", value=f"<@{victim.id}>")
		embed.add_field(name="Moderator", value=f"<@{moderator.id}>")
		embed.add_field(name="Severity", value=f"{severity}")
		embed.add_field(name="Reason", value=f"{reason}")
		if severity == "S2" or severity == "S3":
			embed.add_field(name="Duration", value=f"{duration} (<t:{int((datetime.datetime.now() + utils.parse_duration(duration)).timestamp())}:R>)")
		embed.set_thumbnail(url=victim.avatar)
		log_channel_id = db.get_log_channel(guild.id)
		log_channel = await self.bot.fetch_channel(log_channel_id)
		await log_channel.send(embed=embed)

	@app_commands.command()
	@app_commands.describe(victim="Member to sanction")
	@app_commands.describe(severity="Type of sanction")
	@app_commands.describe(duration="Time of mute (eg: 1s for 1 second, 1m for 1 minute, 1h for 1 hour, 1d for 1 day.)")
	@app_commands.describe(reason="Reason of mute")
	@app_commands.rename(victim='member')
	@app_commands.checks.has_permissions(moderate_members=True)
	async def mute(self,interaction: discord.Interaction, victim: discord.Member, severity: Literal['S2', 'N/A'], duration: str, reason: str):
		if utils.permission_check(moderator=interaction.user, victim=victim, moderation_type="Mute"):
			try:
				guild_id = interaction.guild.id
				user_id = victim.id
				moderator_id = interaction.user.id
				duration_delta = utils.parse_duration(duration)
				moderation_id = db.insert_moderation(guild_id=guild_id, user_id=user_id, moderator_id=moderator_id, moderation_type=reason, severity=severity, duration=duration, time=str(time.time()))
				try:
					channel = await victim.create_dm()
					await channel.send(embed=await embeds.dm_moderation_embed(guild=interaction.guild, victim=victim, reason=reason, duration=duration, severity=severity, moderation_type="Mute"))
				except Exception:
					pass
				await victim.timeout(duration_delta, reason=f"{reason} - {interaction.user.name}", )
				await interaction.response.send_message(f"Moderation `{moderation_id}`: Muted <@{user_id}> for {duration}: **{severity}. {reason}**")
				await moderation.log_embed(self,victim=victim, severity=severity, duration=duration, reason=reason, moderator=interaction.user, moderation_id=moderation_id, moderation_type="Mute", guild=interaction.guild)
			except Exception as e:
				await interaction.response.send_message(f"Unhandled exception caught:\n```\n{e}\n```", ephemeral=True)
		else:
			await interaction.response.send_message("Invalid permissions", ephemeral=True)

	@app_commands.command()
	@app_commands.describe(victim="Member to sanction")
	@app_commands.describe(severity="Type of sanction")
	@app_commands.describe(duration="Time of ban (eg: 1s for 1 second, 1m for 1 minute, 1h for 1 hour, 1d for 1 day.)")
	@app_commands.describe(reason="Reason of ban")
	@app_commands.describe(purge="Purge all messages within 7 days")
	@app_commands.rename(victim='member')
	@app_commands.checks.has_permissions(ban_members=True)
	async def ban(self,interaction: discord.Interaction, victim: discord.Member, severity: Literal['S3', 'S4'], duration: str, reason: str, purge: Literal['No', 'Yes']):
		if utils.permission_check(moderator=interaction.user, victim=victim, moderation_type="Ban"):
			try:
				guild_id = interaction.guild.id
				user_id = victim.id
				moderator_id = interaction.user.id
				moderation_id = db.insert_moderation(guild_id=guild_id, user_id=user_id, moderator_id=moderator_id, moderation_type=reason, severity=severity, duration=duration, time=str(time.time()))
				try:
					channel = await victim.create_dm()
					await channel.send(embed=await embeds.dm_moderation_embed(guild=interaction.guild, victim=victim, reason=reason, duration=duration, severity=severity, moderation_type="Ban"))
				except Exception:
					pass
				await victim.ban(delete_message_days=7, reason=f"{reason} - {interaction.user.name}\nbanned for {duration}")
				if severity == 'S4':
					duration = 'inf'
				await interaction.response.send_message(f"Moderation `{moderation_id}`: Banned <@{user_id}> for **`{duration}`**: **{severity}. {reason}**")
				await moderation.log_embed(self,victim=victim, severity=severity, duration=duration, reason=reason, moderator=interaction.user, moderation_id=moderation_id, moderation_type="Ban", guild=interaction.guild)
			except Exception as e:
				await interaction.response.send_message(f"Unhandled exception caught:\n```\n{e}\n```", ephemeral=True)
		else:
			await interaction.response.send_message("Invalid permissions", ephemeral=True)

	@app_commands.command()
	@app_commands.describe(victim="Member to sanction")
	@app_commands.describe(severity="Type of sanction")
	@app_commands.describe(reason="Reason of warn")
	@app_commands.rename(victim='member')
	@app_commands.checks.has_permissions(moderate_members=True)
	async def warn(self,interaction: discord.Interaction, victim: discord.Member, severity: Literal['S1', 'N/A'], reason: str):
		if utils.permission_check(moderator=interaction.user, victim=victim, moderation_type="Warn"):
			try:
				guild_id = interaction.guild.id
				user_id = victim.id
				moderator_id = interaction.user.id
				moderation_id = db.insert_moderation(guild_id=guild_id, user_id=user_id, moderator_id=moderator_id, moderation_type=reason, severity=severity, duration=None, time=str(time.time()))
				await interaction.response.send_message(f"Moderation `{moderation_id}`: Warned <@{user_id}>: **{severity}. {reason}**")
				try:
					channel = await victim.create_dm()
					await channel.send(embed=await embeds.dm_moderation_embed(guild=interaction.guild, victim=victim, reason=reason, duration=None, severity=severity, moderation_type="Warn"))
				except Exception:
					pass
				await moderation.log_embed(self,victim=victim, severity=severity, duration=None, reason=reason, moderator=interaction.user, moderation_id=moderation_id, moderation_type="Warn", guild=interaction.guild)
			except Exception as e:
				await interaction.response.send_message(f"Unhandled exception caught:\n```\n{e}\n```", ephemeral=True)
		else:
			await interaction.response.send_message("Invalid permissions", ephemeral=True)

async def setup(bot):
	await bot.add_cog(moderation(bot))