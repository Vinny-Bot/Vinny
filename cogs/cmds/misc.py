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
import platform
from discord import app_commands
from discord.ext import commands
import utils.info as info
import utils.db as db
import datetime
import humanfriendly

class misc(commands.Cog):
	def __init__(self, bot: commands.Bot) -> None:
		self.bot = bot

	@app_commands.command(description="Host information")
	async def host_info(self,interaction: discord.Interaction):
		try:
			embed = discord.Embed(title="Host Information", color=16711680, timestamp=datetime.datetime.now())
			embed.add_field(name="Operating System", value=f"{platform.system()} {platform.release()}")
			embed.add_field(name="", value="")
			embed.add_field(name="Python Version", value=f"{platform.python_version()}")
			embed.add_field(name="Vinny Version", value=f"{info.get_vinny_version()}")
			embed.add_field(name="", value="")
			conn, c = db.db_connect()
			embed.add_field(name="Total moderations", value=f"{db.get_count_of_moderations(c)}")
			conn.close()
			await interaction.response.send_message(embed=embed)
		except Exception as e:
			await interaction.response.send_message(f"Unhandled exception caught:\n```\n{e}\n```", ephemeral=True)

	@app_commands.command(description="Say anything in your current channel")
	@app_commands.describe(message="Message to send")
	@app_commands.describe(channel="Channel to send message in")
	@app_commands.describe(reply_to="Message to reply to (give ID)")
	@app_commands.checks.has_permissions(moderate_members=True)
	async def say(self,interaction: discord.Interaction, message: str, channel: discord.TextChannel = None, reply_to: str = None):
		if channel is not None:
			pass
		else:
			channel = interaction.channel
		
		if reply_to is None:
			await interaction.response.send_message(f"Sent message in {channel.mention}", ephemeral=True)
			await channel.send(message)
		else:
			message_obj = await channel.fetch_message(int(reply_to))
			channel = message_obj.channel
			await interaction.response.send_message(f"Sent reply message in {channel.mention} to {message_obj.jump_url}", ephemeral=True)
			await message_obj.reply(message)

	@app_commands.command(description="View bot uptime")
	async def uptime(self,interaction: discord.Interaction):
		timedelta = datetime.datetime.now(datetime.UTC) - self.bot.start_time
		await interaction.response.send_message(content=f"{humanfriendly.format_timespan(timedelta)}")

async def setup(client):
	await client.add_cog(misc(client))