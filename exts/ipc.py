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

from typing import Dict
from discord.ext import commands, ipc
from discord.ext.ipc.server import Server
from discord.ext.ipc.objects import ClientPayload

class Routes(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot
		if not hasattr(bot, "ipc"):
			bot.ipc = ipc.Server(self.bot, secret_key="🐼")
	
	async def cog_load(self) -> None:
		await self.bot.ipc.start()

	async def cog_unload(self) -> None:
		await self.bot.ipc.stop()
		self.bot.ipc = None

async def setup(bot):
	await bot.add_cog(Routes(bot))