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
import os
import asyncio
from discord import app_commands
from discord import Guild, User
from discord.ext import commands
from pathlib import Path
import sys
import datetime
import time
import schedule
from utils import db
from utils import embeds

base_dir = Path(__file__).resolve().parent

if sys.version_info >= (3, 11): # compat with older python (you'll need to install tomli from pip though)
	import tomllib
else:
	import tomli as tomllib

class bot(commands.Bot):
	def __init__(self) -> None:
		intents = discord.Intents.all()
		intents.emojis_and_stickers = False
		allowed_mentions = discord.AllowedMentions(everyone=False, roles=False, users=True)
		super().__init__(
			intents=intents,
			max_messages=5000,
			command_prefix=None,
			allowed_mentions=allowed_mentions,
			activity=discord.Activity(type=discord.ActivityType.listening, name="your every move")
		)

bot = bot()

tree = bot.tree

def load_config():
	try:
		with open("config.toml", "rb") as f: # load config
			config_data = tomllib.load(f)
			return config_data
	except tomllib.TOMLDecodeError: # incase config is literally invalid
		print("Invalid TOML configuration detected, make sure to follow the config guide in the README.md")
		return None

config_data = load_config()
token = config_data['discord']['token']
message_delete_embeds = {} # this is so we can send one message with all the embeds
intents = discord.Intents.default()

@bot.event
async def on_ready():
	print(f'logged in to {bot.user}')
	try:
		synced = await tree.sync()
		print(f"synced {len(synced)} commands")
		print("starting scheduler")
		await scheduler()
	except Exception as e:
		print(f"Error while initializing bot: {e}")

@bot.event
async def on_raw_message_delete(payload: discord.RawMessageDeleteEvent):
	global message_delete_embeds
	if payload.guild_id not in message_delete_embeds:
		message_delete_embeds[payload.guild_id] = []
		
	embed = await embeds.delete_message_embed(payload, payload.cached_message)
	message_delete_embeds[payload.guild_id].append(embed)

@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
	if before.content == after.content:
		return
	channel_id = db.get_event_log_channel(before.guild.id)
	channel = await bot.fetch_channel(channel_id)
	embed = await embeds.edit_message_embed(before, after)
	await channel.send(embed=embed)

@bot.event
async def on_raw_message_edit(payload: discord.RawMessageUpdateEvent):
	if payload.cached_message is None:
		channel_id = db.get_event_log_channel(payload.guild_id)
		channel = await bot.fetch_channel(channel_id)
		event_channel = await bot.fetch_channel(payload.channel_id)
		message = await event_channel.fetch_message(payload.message_id)
		embed = await embeds.raw_edit_message_embed(payload=payload, message=message)
		await channel.send(embed=embed)

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
	channel_id = db.get_event_log_channel(before.guild.id)
	channel = await bot.fetch_channel(channel_id)
	embed = await embeds.member_update_embed(before, after)
	await channel.send(embed=embed)

@bot.event
async def on_guild_channel_create(event_channel):
	channel_id = db.get_event_log_channel(event_channel.guild.id)
	channel = await bot.fetch_channel(channel_id)
	embed = await embeds.channel_created(event_channel)
	await channel.send(embed=embed)

@bot.event
async def on_guild_channel_delete(event_channel):
	channel_id = db.get_event_log_channel(event_channel.guild.id)
	channel = await bot.fetch_channel(channel_id)
	embed = await embeds.channel_deleted(event_channel)
	await channel.send(embed=embed)

@bot.event
async def on_member_join(member: discord.Member):
	channel = await bot.fetch_channel(db.get_event_log_channel(member.guild.id))
	embed = await embeds.member_join(member)
	await channel.send(embed=embed)

@bot.event
async def on_member_remove(member: discord.Member):
	channel = await bot.fetch_channel(db.get_event_log_channel(member.guild.id))
	embed = await embeds.member_remove(member)
	await channel.send(embed=embed)

async def loadcogs():
	command_path = base_dir / 'cmds'
	for files in os.listdir(command_path):
		if files.endswith(".py"):
			await bot.load_extension(f'cmds.{files[:-3]}')
	extensions_path = base_dir / 'exts'
	for files in os.listdir(extensions_path):
		if files.endswith(".py"):
			await bot.load_extension(f'exts.{files[:-3]}')

async def init():
	async with bot:
		await loadcogs()
		await bot.start(token)

async def look_for_unbans(): # check every active tempban for an unban
	unbans = db.get_active_tempbans()
	now = datetime.datetime.now()

	try:
		for uban in unbans:
			if uban['unban_time'] <= now:
				# if we have a moderation that's past (or equal) to its unban time we will start the unban process
				moderation = db.get_moderation_by_id(uban['moderation_id'])

				if moderation:
					guild_id = moderation[1]
					user_id = moderation[2]

					user = await bot.fetch_user(int(user_id))
					guild = await bot.fetch_guild(int(guild_id))
					try:
						await guild.unban(user, reason="Scheduled unban")
					except Exception:
						pass
					db.set_tempban_inactive(uban['moderation_id'])
					print(f"Unbanned {user.name} from {guild.name}")
	except Exception as e:
		print(f"Error while unbanning: {e}")

async def send_pending_delete_events():
	for guild_id, embeds in message_delete_embeds.items():
		channel_id = db.get_event_log_channel(guild_id)
		try:
			channel = await bot.fetch_channel(channel_id)
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

schedule.every().minute.do(lambda: asyncio.create_task(look_for_unbans()))
schedule.every(10).seconds.do(lambda: asyncio.create_task(send_pending_delete_events()))

async def scheduler():
	while True:
		await asyncio.sleep(1)
		schedule.run_pending()

asyncio.run(init())