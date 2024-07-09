# vinny - discord moderation bot
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
import Paginator
import importlib

class moderation(commands.Cog):
	def __init__(self, bot: commands.Bot) -> None:
		self.bot = bot

	async def log_embed(self,victim: discord.Member, severity: str, duration: str, reason: str, moderator: discord.Member, moderation_id: str, moderation_type: str, guild: discord.Guild):
		embed = discord.Embed(title=f"Moderation `{moderation_id}` - {moderation_type}", color=16711680, timestamp=datetime.datetime.now())
		embed.add_field(name="Moderated member", value=f"<@{victim.id}>")
		embed.add_field(name="Moderator", value=f"<@{moderator.id}>")
		if moderation_type != "Kick" and moderation_type != "Unmute":
			embed.add_field(name="Severity", value=f"{severity}")
		embed.add_field(name="Reason", value=f"{reason}")
		if moderation_type == "Mute" or severity == "S3":
			embed.add_field(name="Duration", value=f"{duration} (<t:{int((datetime.datetime.now() + utils.parse_duration(duration)).timestamp())}:R>)")
		embed.set_thumbnail(url=victim.avatar)
		conn, c = db.db_connect()
		log_channel_id = db.get_config_value(guild.id, "log_channel_id", c, 0)
		conn.close()
		log_channel = await self.bot.fetch_channel(log_channel_id)
		await log_channel.send(embed=embed)

	@app_commands.command(description="Mute a member")
	@app_commands.describe(victim="Member to sanction")
	@app_commands.describe(severity="Type of sanction")
	@app_commands.describe(duration="Time of mute (eg: 1s for 1 second, 1m for 1 minute, 1h for 1 hour, 1d for 1 day.)")
	@app_commands.describe(reason="Reason of mute")
	@app_commands.rename(victim='member')
	@app_commands.checks.has_permissions(moderate_members=True)
	async def mute(self,interaction: discord.Interaction, victim: discord.Member, severity: Literal['S2', 'N/A'], duration: str, reason: str):
		success, message = utils.permission_check(interaction.user, victim, "Mute")
		if success:
			try:
				guild_id = interaction.guild.id
				user_id = victim.id
				moderator_id = interaction.user.id
				try:
					duration_delta = utils.parse_duration(duration)
				except Exception:
					await interaction.response.send_message("Please input a valid timeframe (eg: 1s, 1m, 1h, 1d)", ephemeral=True)
					return
				conn, c = db.db_connect()
				moderation_id = db.insert_moderation(guild_id=guild_id, user_id=user_id, moderator_id=moderator_id, moderation_type="Mute", reason=reason, severity=severity, duration=duration, time=str(time.time()), conn=conn, c=c)
				conn.close()
				try:
					channel = await victim.create_dm()
					await channel.send(embed=await embeds.dm_moderation_embed(guild=interaction.guild, victim=victim, reason=reason, duration=duration, severity=severity, moderation_type="Mute"))
				except Exception:
					pass
				await victim.timeout(duration_delta, reason=f"{reason} - {interaction.user.name}")
				await interaction.response.send_message(f"Moderation `{moderation_id}`: Muted <@{user_id}> for **`{duration}`**: **{severity}. {reason}**")
				await moderation.log_embed(self,victim=victim, severity=severity, duration=duration, reason=reason, moderator=interaction.user, moderation_id=moderation_id, moderation_type="Mute", guild=interaction.guild)
			except Exception as e:
				await interaction.response.send_message(f"Unhandled exception caught:\n```\n{e}\n```", ephemeral=True)
		else:
			await interaction.response.send_message(message, ephemeral=True)

	@app_commands.command(description="Ban a member")
	@app_commands.describe(victim="Member to sanction")
	@app_commands.describe(severity="Type of sanction (S3 = Tempban, S4 = Permban)")
	@app_commands.describe(duration="Time of ban (eg: 1s for 1 second, 1m for 1 minute, 1h for 1 hour, 1d for 1 day.)")
	@app_commands.describe(reason="Reason of ban")
	@app_commands.describe(purge="Purge all messages within 7 days")
	@app_commands.rename(victim='member')
	async def ban(self,interaction: discord.Interaction, victim: discord.Member, severity: Literal['S3', 'S4'], reason: str, purge: Literal['No', 'Yes'], duration: str = None):
		success, message = utils.permission_check(interaction.user, victim, "Ban")
		if success:
			try:
				guild_id = interaction.guild.id
				user_id = victim.id
				moderator_id = interaction.user.id
				if severity == 'S4':
					duration = 'N/A'
				else:
					if duration is not None:
						try:
							newdur = utils.parse_duration(duration)
						except Exception:
							return await interaction.response.send_message("Please input a valid timeframe (eg: 1s, 1m, 1h, 1d)", ephemeral=True)
					else:
						return await interaction.response.send_message("Please input a valid timeframe (eg: 1s, 1m, 1h, 1d)", ephemeral=True)
				conn, c = db.db_connect()
				moderation_id = db.insert_moderation(guild_id=guild_id, user_id=user_id, moderator_id=moderator_id, moderation_type="Ban", reason=reason, severity=severity, duration=duration, time=str(time.time()), conn=conn, c=c)
				conn.close()
				if purge == "No":
					delete_days = 0
				else:
					delete_days = 7
				try:
					channel = await victim.create_dm()
					await channel.send(embed=await embeds.dm_moderation_embed(guild=interaction.guild, victim=victim, reason=reason, duration=duration, severity=severity, moderation_type="Ban"))
				except Exception:
					pass
				await victim.ban(delete_message_days=delete_days, reason=f"{reason} - {interaction.user.name}\nbanned for {duration}")
				await interaction.response.send_message(f"Moderation `{moderation_id}`: Banned <@{user_id}> for **`{duration}`**: **{severity}. {reason}**")
				await moderation.log_embed(self,victim=victim, severity=severity, duration=duration, reason=reason, moderator=interaction.user, moderation_id=moderation_id, moderation_type="Ban", guild=interaction.guild)
			except Exception as e:
				await interaction.response.send_message(f"Unhandled exception caught:\n```\n{e}\n```", ephemeral=True)
		else:
			await interaction.response.send_message(message, ephemeral=True)

	@app_commands.command(description="Warn a member")
	@app_commands.describe(victim="Member to sanction")
	@app_commands.describe(severity="Type of sanction")
	@app_commands.describe(reason="Reason of warn")
	@app_commands.rename(victim='member')
	async def warn(self,interaction: discord.Interaction, victim: discord.Member, severity: Literal['S1', 'N/A'], reason: str):
		success, message = utils.permission_check(interaction.user, victim, "Warn")
		if success:
			try:
				guild_id = interaction.guild.id
				user_id = victim.id
				moderator_id = interaction.user.id
				conn, c = db.db_connect()
				moderation_id = db.insert_moderation(guild_id=guild_id, user_id=user_id, moderator_id=moderator_id, moderation_type="Warn", reason=reason, severity=severity, duration=None, time=str(time.time()), conn=conn, c=c)
				conn.close()
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
			await interaction.response.send_message(message, ephemeral=True)

	@app_commands.command(description="Kick a member")
	@app_commands.describe(victim="Member to sanction")
	@app_commands.describe(reason="Reason of kick")
	@app_commands.rename(victim='member')
	async def kick(self,interaction: discord.Interaction, victim: discord.Member, reason: str):
		success, message = utils.permission_check(interaction.user, victim, "Kick")
		if success:
			try:
				guild_id = interaction.guild.id
				user_id = victim.id
				moderator_id = interaction.user.id
				conn, c = db.db_connect()
				moderation_id = db.insert_moderation(guild_id=guild_id, user_id=user_id, moderator_id=moderator_id, moderation_type="Kick", reason=reason, severity="N/A", duration=None, time=str(time.time()), conn=conn, c=c)
				conn.close()
				await interaction.response.send_message(f"Moderation `{moderation_id}`: Kicked <@{user_id}>: **{reason}**")
				try:
					channel = await victim.create_dm()
					await channel.send(embed=await embeds.dm_moderation_embed(guild=interaction.guild, victim=victim, reason=reason, duration=None, severity="N/A", moderation_type="Kick"))
				except Exception:
					pass
				await victim.kick()
				await moderation.log_embed(self,victim=victim, severity="N/A", duration=None, reason=reason, moderator=interaction.user, moderation_id=moderation_id, moderation_type="Kick", guild=interaction.guild)
			except Exception as e:
				await interaction.response.send_message(f"Unhandled exception caught:\n```\n{e}\n```", ephemeral=True)
		else:
			await interaction.response.send_message(message, ephemeral=True)

	@app_commands.command(description="Unmute a member")
	@app_commands.describe(victim="Member to unmute")
	@app_commands.describe(reason="Reason of unmute")
	@app_commands.rename(victim='member')
	async def unmute(self,interaction: discord.Interaction, victim: discord.Member, reason: str = "Unmuted"):
		success, message = utils.permission_check(interaction.user, victim, "Mute")
		if success:
			try:
				guild_id = interaction.guild.id
				user_id = victim.id
				moderator_id = interaction.user.id
				conn, c = db.db_connect()
				moderation_id = db.insert_moderation(guild_id=guild_id, user_id=user_id, moderator_id=moderator_id, moderation_type="Unmute", reason=reason, severity="N/A", duration=None, time=str(time.time()), conn=conn, c=c)
				conn.close()
				await interaction.response.send_message(f"Moderation `{moderation_id}`: Unmuted <@{user_id}>: **{reason}**")
				try:
					channel = await victim.create_dm()
					await channel.send(embed=await embeds.dm_moderation_embed(guild=interaction.guild, victim=victim, reason=reason, duration=None, severity="N/A", moderation_type="Unmute"))
				except Exception:
					pass
				await victim.timeout(utils.parse_duration("0s"), reason=f"{reason} - Unmuted by {interaction.user.name}")
				await moderation.log_embed(self,victim=victim, severity="N/A", duration=None, reason=reason, moderator=interaction.user, moderation_id=moderation_id, moderation_type="Unmute", guild=interaction.guild)
			except Exception as e:
				await interaction.response.send_message(f"Unhandled exception caught:\n```\n{e}\n```", ephemeral=True)
		else:
			await interaction.response.send_message(message, ephemeral=True)

	@app_commands.command(description="Unban a member")
	@app_commands.describe(victim="Member to unban (Provide ID if you can't pick the user)")
	@app_commands.describe(reason="Reason of unban")
	@app_commands.rename(victim='user') # renamed from member to user for accuracy 🔥
	async def unban(self,interaction: discord.Interaction, victim: discord.User, reason: str = "Unbanned"):
		success, message = utils.permission_check(interaction.user, victim, "Ban")
		if success:
			try:
				guild_id = interaction.guild.id
				user_id = victim.id
				moderator_id = interaction.user.id
				try:
					await interaction.guild.fetch_ban(victim)
				except Exception:
					return await interaction.response.send_message(f"This user isn't banned", ephemeral=True)
				conn, c = db.db_connect()
				moderation_id = db.insert_moderation(guild_id=guild_id, user_id=user_id, moderator_id=moderator_id, moderation_type="Unban", reason=reason, severity="N/A", duration=None, time=str(time.time()), conn=conn, c=c)
				conn.close()
				await interaction.response.send_message(f"Moderation `{moderation_id}`: Unbanned <@{user_id}>: **{reason}**")
				await interaction.guild.unban(user=victim, reason=f"{reason} - Unbanned by {interaction.user.name}")
				try:
					channel = await victim.create_dm()
					await channel.send(embed=await embeds.dm_moderation_embed(guild=interaction.guild, victim=victim, reason=reason, duration=None, severity="N/A", moderation_type="Unban"))
				except Exception:
					pass
				await moderation.log_embed(self,victim=victim, severity="N/A", duration=None, reason=reason, moderator=interaction.user, moderation_id=moderation_id, moderation_type="Unban", guild=interaction.guild)
			except Exception as e:
				await interaction.response.send_message(f"Unhandled exception caught:\n```\n{e}\n```", ephemeral=True)
		else:
			await interaction.response.send_message(message, ephemeral=True)

	@app_commands.command(description="View moderations of a member")
	@app_commands.describe(inactive="View inactive moderations as well")
	@app_commands.rename(inactive="view_inactive")
	async def moderations(self,interaction: discord.Interaction, member: discord.User, inactive: bool = False):
		pages = []
		page = 1
		conn, c = db.db_connect()
		moderations = db.get_moderations_by_user_and_guild(interaction.guild.id, member.id, inactive, c)
		conn.close()
		try:
			for i in range(0, len(moderations), 6):
				embed = discord.Embed(title=f"{member.name}'s moderations", description=f"Page {page}")
				chunk = moderations[i:i+6]
				page = page + 1
				for moderation in chunk:
					if moderation[8] is None:
						duration = ""
					else:
						duration = f" `{moderation[8]}`"
					if moderation[9] == 0:
						embed.add_field(name=f"⛔️ {moderation[4]} ({moderation[6]}) - `{moderation[0]}`", value=f"`{moderation[5]}`\n<@{moderation[3]}>\n<t:{int(float(moderation[7]))}>{duration}")
					else:
						embed.add_field(name=f"{moderation[4]} ({moderation[6]}) - `{moderation[0]}`", value=f"`{moderation[5]}`\n<@{moderation[3]}>\n<t:{int(float(moderation[7]))}>{duration}")
				pages.append(embed)
			await Paginator.Simple().start(interaction, pages=pages)
		except Exception:
			await interaction.response.send_message("This member doesn't have any moderations in this server", ephemeral=True)

	@app_commands.command(description="Mark moderation as inactive or active")
	@app_commands.rename(moderation_id='moderation')
	@app_commands.describe(moderation_id="Moderation to mark inactive (Provide ID)")
	@app_commands.checks.has_permissions(moderate_members=True)
	async def mark_moderation(self,interaction: discord.Interaction, moderation_id: int, mark: Literal["Inactive", "Active"]):
		conn, c = db.db_connect()
		moderation = db.get_moderation_by_id(moderation_id, c)
		if moderation is not None and moderation[1] == interaction.guild.id:
			if mark == "Inactive":
				active = False
			else:
				active = True
			try:
				db.set_moderation_inactive_or_active(moderation_id, active, conn, c)
				await interaction.response.send_message(f"Marked moderation `{moderation_id}` as {mark}")
			except Exception as e:
				await interaction.response.send_message(f"Unhandled exception caught:\n```\n{e}\n```", ephemeral=True)
		else:
			await interaction.response.send_message(f"Invalid moderation", ephemeral=True)
		conn.close()

	@app_commands.command(description="View info about a moderation")
	@app_commands.rename(moderation_id='moderation')
	@app_commands.describe(moderation_id="Moderation to view")
	async def moderation(self,interaction: discord.Interaction, moderation_id: int):
		conn, c = db.db_connect()
		moderation = db.get_moderation_by_id(moderation_id, c)
		conn.close()
		if moderation is not None and moderation[1] == interaction.guild.id:
			if moderation[9] == 0:
				active = "No"
			else:
				active = "Yes"
			try:
				embed = discord.Embed(title=f"Moderation `{moderation_id}`", timestamp=datetime.datetime.now())
				embed.add_field(name="Victim", value=f"<@{moderation[2]}>\n{moderation[2]}")
				embed.add_field(name="Moderator", value=f"<@{moderation[3]}>\n{moderation[3]}")
				embed.add_field(name="Type", value=f"{moderation[4]}")
				embed.add_field(name="Sanction", value=f"{moderation[6]}")
				embed.add_field(name="Reason", value=f"{moderation[5]}")
				embed.add_field(name="Duration", value=f"{moderation[8]}")
				embed.add_field(name="Time", value=f"<t:{int(float(moderation[7]))}>")
				embed.add_field(name="Active", value=f"{active}")
				await interaction.response.send_message(embed=embed)
			except Exception as e:
				print(e)
		else:
			await interaction.response.send_message(f"Invalid moderation", ephemeral=True)

	@app_commands.command(description="Change moderation reason")
	@app_commands.rename(moderation_id='moderation')
	@app_commands.describe(moderation_id="Moderation to change reason of (Provide ID)")
	@app_commands.describe(new_reason="New moderation reason")
	@app_commands.checks.has_permissions(moderate_members=True)
	async def reason(self,interaction: discord.Interaction, moderation_id: int, new_reason: str, notify: bool = True):
		conn, c = db.db_connect()
		moderation = db.get_moderation_by_id(moderation_id, c)
		if moderation is not None and moderation[1] == interaction.guild.id:
			try:
				notified = "notified of this change"
				if not notify:
					notified = "not notified of this change"
				c.execute('SELECT reason FROM moderations WHERE moderation_id=?', (moderation_id,))
				old_reason = c.fetchone()[0]
				c.execute('UPDATE moderations SET reason=? WHERE moderation_id=?', (new_reason, moderation_id,))
				conn.commit()
				await interaction.response.send_message(f"Updated moderation `{moderation_id}`: Reason changed from `{old_reason}` to `{new_reason}`. The user was {notified}")
				embed = await embeds.moderation_change_reason(interaction.user, moderation_id, moderation[4], new_reason, old_reason)
				log_channel_id = db.get_config_value(interaction.guild.id, "log_channel_id", c, 0)
				log_channel = await self.bot.fetch_channel(log_channel_id)
				await log_channel.send(embed=embed)
				if notify:
					try:
						victim = await interaction.guild.fetch_member(moderation[2])
						channel = await victim.create_dm()
						await channel.send(embed=embed)
					except Exception:
						pass
			except Exception as e:
				await interaction.response.send_message(f"Unhandled exception caught:\n```\n{e}\n```", ephemeral=True)
		else:
			await interaction.response.send_message(f"Invalid moderation", ephemeral=True)
		conn.close()

async def setup(bot):
	importlib.reload(db)
	importlib.reload(utils)
	importlib.reload(embeds)
	await bot.add_cog(moderation(bot))