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
import os
import asyncio
from discord.ext import commands
from pathlib import Path
from utils import utils
import sys

base_dir = Path(__file__).resolve().parent

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

config_data = utils.load_config()
token = config_data['discord']['token']
intents = discord.Intents.default()

@bot.event
async def on_ready():
	print(f'logged in to {bot.user}')
	try:
		synced = await tree.sync()
		print(f"synced {len(synced)} commands")
	except Exception as e:
		print(f"Error while initializing bot: {e}")

async def loadcogs():
	command_path = base_dir / 'cmds'
	for files in os.listdir(command_path):
		if files.endswith(".py"):
			await bot.load_extension(f'cmds.{files[:-3]}')
	extensions_path = base_dir / 'exts'
	for files in os.listdir(extensions_path):
		if files.endswith(".py"):
			if files[:-3] != "ipc":
				await bot.load_extension(f'exts.{files[:-3]}')
			elif files[:-3] == "ipc" and "--enable-ipc" in sys.argv:
				await bot.load_extension(f'exts.{files[:-3]}')
				print("IPC extension enabled")

async def init():
	async with bot:
		await loadcogs()
		await bot.start(token)

asyncio.run(init())