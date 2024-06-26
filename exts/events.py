# vinny - discord moderation self.bot
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
from discord.ext.commands import Bot
from typing import Literal
import discord.ext
import discord.ext.commands
import discord.ext.commands.view
import schedule
import asyncio
from utils import db, utils, embeds
from cmds import moderation
import datetime
import time
import traceback
message_delete_embeds = {} # this is so we can send one message with all the embeds

class events(commands.Cog):
	def __init__(self, bot: commands.Bot) -> None:
		self.bot = bot

	async def send_pending_delete_events(self):
		for guild_id, embeds in message_delete_embeds.items():
			conn, c = db.db_connect()
			channel_id = db.get_event_log_channel(guild_id, c)
			conn.close()
			try:
				channel = await self.bot.fetch_channel(channel_id)
			except Exception as e:
				channel = None
				del message_delete_embeds[guild_id]
				return
			# send in batches of 10 embeds so that api doesnt get mad
			for i in range(0, len(embeds), 10):
				batch = embeds[i:i+10]
				await channel.send(embeds=batch)
				
				# delete the sent embeds from the dictionary and then wait for another schedule job to send & delete the rest
				del message_delete_embeds[guild_id][i:i+10]

	async def scheduler(self):
		while True:
			await asyncio.sleep(1)
			schedule.run_pending()

	async def start_schedule(self):
		schedule.every(10).seconds.do(lambda: asyncio.create_task(events.send_pending_delete_events(self)))

	@commands.Cog.listener()
	async def on_ready(self):
		await events.start_schedule(self)
		await events.scheduler(self)

	@commands.Cog.listener()
	async def on_raw_message_delete(self,payload: discord.RawMessageDeleteEvent):
		global message_delete_embeds
		if payload.guild_id not in message_delete_embeds:
			message_delete_embeds[payload.guild_id] = []
			
		embed = await embeds.delete_message_embed(payload, payload.cached_message)
		message_delete_embeds[payload.guild_id].append(embed)

	@commands.Cog.listener()
	async def on_message_edit(self,before: discord.Message, after: discord.Message):
		if before.content == after.content:
			return
		conn, c = db.db_connect()
		channel_id = db.get_event_log_channel(before.guild.id, c)
		conn.close()
		channel = await self.bot.fetch_channel(channel_id)
		embed = await embeds.edit_message_embed(before, after)
		await channel.send(embed=embed)

	@commands.Cog.listener()
	async def on_raw_message_edit(self,payload: discord.RawMessageUpdateEvent):
		if payload.cached_message is None:
			conn, c = db.db_connect()
			channel_id = db.get_event_log_channel(payload.guild_id, c)
			conn.close()
			channel = await self.bot.fetch_channel(channel_id)
			event_channel = await self.bot.fetch_channel(payload.channel_id)
			message = await event_channel.fetch_message(payload.message_id)
			embed = await embeds.raw_edit_message_embed(payload=payload, message=message)
			await channel.send(embed=embed)

	@commands.Cog.listener()
	async def on_member_update(self,before: discord.Member, after: discord.Member):
		conn, c = db.db_connect()
		channel_id = db.get_event_log_channel(before.guild.id, c)
		conn.close()
		channel = await self.bot.fetch_channel(channel_id)
		embed = await embeds.member_update_embed(before, after)
		await channel.send(embed=embed)

	@commands.Cog.listener()
	async def on_guild_channel_create(self,event_channel):
		conn, c = db.db_connect()
		channel_id = db.get_event_log_channel(event_channel.guild.id, c)
		conn.close()
		channel = await self.bot.fetch_channel(channel_id)
		embed = await embeds.channel_created(event_channel)
		await channel.send(embed=embed)

	@commands.Cog.listener()
	async def on_guild_channel_delete(self,event_channel):
		conn, c = db.db_connect()
		channel_id = db.get_event_log_channel(event_channel.guild.id, c)
		conn.close()
		channel = await self.bot.fetch_channel(channel_id)
		embed = await embeds.channel_deleted(event_channel)
		await channel.send(embed=embed)

	@commands.Cog.listener()
	async def on_member_join(self,member: discord.Member):
		conn, c = db.db_connect()
		channel = await self.bot.fetch_channel(db.get_event_log_channel(member.guild.id, c))
		conn.close()
		embed = await embeds.member_join(member)
		await channel.send(embed=embed)

	@commands.Cog.listener()
	async def on_member_remove(self,member: discord.Member):
		conn, c = db.db_connect()
		channel = await self.bot.fetch_channel(db.get_event_log_channel(member.guild.id, c))
		conn.close()
		embed = await embeds.member_remove(member)
		await channel.send(embed=embed)

async def setup(bot):
	await bot.add_cog(events(bot))