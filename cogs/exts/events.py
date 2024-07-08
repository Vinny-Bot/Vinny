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
import datetime
import time
import traceback
import importlib
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

	@commands.Cog.listener()
	async def on_message(self,message: discord.Message):
			if isinstance(message.nonce, str) and not message.nonce.isdigit():
				conn, c = db.db_connect()
				nonce_filtering = db.get_nonce_filter_status(message.guild.id, c)
				if nonce_filtering == 1:
					try:
						channel = await self.bot.fetch_channel(db.get_log_channel(message.guild.id, c))
						await message.delete()
						embed = discord.Embed(title="Hidden nonce message detected", color=16729932, timestamp=datetime.datetime.now())
						embed.add_field(name="Author", value=f"<@{message.author.id}>\n{message.author.id}")
						embed.add_field(name="Channel", value=f"<#{message.channel.id}>\n{message.channel.id}")
						embed.add_field(name="Message ID", value=message.id)
						embed.add_field(name="Message contents", value=f"```\n{message.content}\n```")
						embed.add_field(name="Nonce contents", value=f"```\n{message.nonce}\n```")
						embed.set_thumbnail(url=message.author.avatar)
						await channel.send(embed=embed)
						conn.close()
					except Exception as e:
						print(e)
						conn.close()

	@commands.Cog.listener()
	async def on_guild_remove(self,guild: discord.Guild):
		try:
			conn, c = db.db_connect()
			c.execute('DELETE FROM guilds WHERE guild_id = ?', (guild.id,))
			conn.commit()
			conn.close()
		except Exception:
			pass

async def setup(bot):
	importlib.reload(utils)
	importlib.reload(db)
	importlib.reload(embeds)
	await bot.add_cog(events(bot))