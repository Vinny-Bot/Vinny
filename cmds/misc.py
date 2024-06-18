import discord
import platform
from discord import app_commands
from discord.ext import commands
import utils.info as info
import utils.db as db

class misc(commands.Cog):
	@app_commands.command()
	async def host_info(self,interaction: discord.Interaction):
		try:
			embed = discord.Embed(title="Host Information", color=16711680)
			embed.add_field(name="Operating System", value=f"{platform.system()} {platform.release()}")
			embed.add_field(name="", value="")
			embed.add_field(name="Python Version", value=f"{platform.python_version()}")
			embed.add_field(name="Pakmar Version", value=f"{info.get_pakmar_version()}")
			embed.add_field(name="", value="")
			embed.add_field(name="Total moderations", value=f"{db.get_count_of_moderations()}")
			await interaction.response.send_message(embed=embed)
		except Exception as e:
			await interaction.response.send_message("Unhandled exception caught:\n```\n{e}\n```", ephemeral=True)

async def setup(client):
	await client.add_cog(misc(client))