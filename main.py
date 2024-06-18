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
from discord.ext import commands
from pathlib import Path
import sys

base_dir = Path(__file__).resolve().parent

if sys.version_info >= (3, 11): # compat with older python (you'll need to install tomli from pip though)
	import tomllib
else:
	import tomli as tomllib

bot = commands.Bot(command_prefix="pak!", intents=discord.Intents.all())
tree = bot.tree

def load_config():
	try:
		with open("config.toml", "rb") as f: # load config
			config_data = tomllib.load(f)
			return config_data
	except tomllib.TOMLDecodeError: # incase config is literally invalid
		print("Invalid TOML configuration detected, make sure to follow the config guide in URL.HERE.FIXME.YEA")
		return None

config_data = load_config()
token = config_data['discord']['token']

intents = discord.Intents.default()

@bot.event
async def on_ready():
	print(f'logged in to {bot.user}')
	try:
		synced = await tree.sync()
		print(f"synced {len(synced)} commands")
	except Exception:
		print(Exception)

async def loadcmds():
	command_path = base_dir / 'cmds'
	for files in os.listdir(command_path):
		if files.endswith(".py"):
			await bot.load_extension(f'cmds.{files[:-3]}')

async def init():
	async with bot:
		await loadcmds()	
		await bot.start(token)

asyncio.run(init())