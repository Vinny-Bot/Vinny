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
#
# NOTE: If you wanna use my dashboard module/IPC extension without complying with above terms,
# then contact me for inquiries/questions for permission. You will only be able to
# use my commits if you have received permission from me. <0vfx@proton.me>

from typing import Dict
import discord
from discord import app_commands
from discord.ext import commands, ipc
from discord.ext.ipc.server import Server
from discord.ext.ipc.objects import ClientPayload
from utils import utils
import importlib
import asyncio

class Routes(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot
		if not hasattr(self, "ipc"):
			config_data = utils.load_config()
			self.ipc = ipc.Server(self.bot, secret_key=config_data['dashboard']['ipc_secret'])
	
	async def cog_load(self) -> None:
		asyncio.create_task(self.ipc.start())

	async def cog_unload(self) -> None:
		await self.ipc.stop()
		self.ipc = None

	@Server.route()
	async def get_guild_ids(self, data):
		guild_ids = []
		for guild in self.bot.guilds:
			guild_ids.append(guild.id)
		guild_ids = repr(guild_ids)
		return guild_ids

	@Server.route()
	async def get_guild_name(self, data):
		guild_id = data['guild_id']
		guild = self.bot.get_guild(guild_id)
		return guild.name

	@Server.route()
	async def get_guild_channels(self, data):
		guild_id = data['guild_id']
		guild = self.bot.get_guild(guild_id)
		if guild is not None:
			channels = {channel.id: channel.name for channel in guild.channels if not isinstance(channel, (discord.CategoryChannel, discord.VoiceChannel))}
			return channels
		else:
			return {}

	@Server.route()
	async def check_admin(self, data):
		guild_id = data['guild_id']
		user_id = data['user_id']
		guild = self.bot.get_guild(guild_id)
		member = guild.get_member(user_id)
		if member is None:
			return False
		
		if member.guild_permissions.administrator:
			return repr(True)
		else:
			return repr(False)

	@Server.route()
	async def get_username(self, data):
		try:
			user = self.bot.get_user(data['user_id'])
			if user is None:
				username = (await self.bot.fetch_user(data['user_id'])).name
			else:
				username = user.name
		except Exception:
			pass
		if username is None:
			username = data['id'].id
		return username

	@app_commands.command(description="View moderations in this server")
	async def server_moderations(self,interaction: discord.Interaction):
		config_data = utils.load_config()
		await interaction.response.send_message(content=f"[Click me!]({config_data['dashboard']['url']}/dashboard/server/{interaction.guild.id}/moderations)")

async def setup(bot):
	importlib.reload(utils)
	await bot.add_cog(Routes(bot))