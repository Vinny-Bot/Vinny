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
# This example requires the 'message_content' intent.

import discord
from discord import app_commands
from discord.ext import commands
import sys

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

@tree.command(name="test")
async def test(interaction: discord.Interaction):
	await interaction.response.send_message("Test")

bot.run(token)
