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

# NOTE: If you wanna use my dashboard module without complying with above terms,
# then contact me for inquiries/questions for permission. You will only be able to
# use my commits if you have received permission from me. <0vfx@proton.me>

import asyncio
from datetime import datetime
from time import strftime
from flask import Flask, render_template, redirect, request, url_for
from flask_discord import DiscordOAuth2Session, requires_authorization, Unauthorized, models
from discord.ext.ipc import Client
from discord import Guild
import sys
import os
sys.path.append(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')))
from utils import utils, db, info
from ast import literal_eval

dashboard_version = "1.0.0"

app = Flask(__name__)

config_data = utils.load_config()
app.secret_key = config_data['dashboard']['secret']

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "false" # Set to true only in development

app.config["DISCORD_CLIENT_TOKEN"] = config_data['discord']['token']
app.config["DISCORD_CLIENT_SECRET"] = config_data['discord']['secret']
app.config["DISCORD_CLIENT_ID"] = config_data['discord']['id']
app.config["DISCORD_REDIRECT_URI"] = f"{config_data['dashboard']['url']}/callback"

app.config['TEMPLATES_AUTO_RELOAD'] = True

OAuth2 = DiscordOAuth2Session(app)
ipc = Client(secret_key=config_data['dashboard']['ipc_secret'])

@app.route('/')
def index():
	user = None
	if OAuth2.authorized:
		user = OAuth2.fetch_user()
	return render_template('index.html', user=user, authorized=OAuth2.authorized)

@app.context_processor
def inject_global_vars():
	return {'dashboard_version': dashboard_version, 'version': info.get_vinny_version()}

@app.route("/login/")
def login():
	return OAuth2.create_session()

@app.route("/logout/")
def logout():
	OAuth2.revoke()
	return redirect(url_for("index"))

@app.route("/callback/")
def callback():
	try:
		OAuth2.callback()
	except Exception:
		return redirect(url_for("dashboard"))
	return redirect(url_for("index"))

@app.errorhandler(Unauthorized)
def redirect_unauthorized(e):
	return redirect(url_for("login"))

@app.route("/dashboard/")
@requires_authorization
def dashboard():
	user = OAuth2.fetch_user()
	guilds = OAuth2.fetch_guilds() # use cache instead of user.fetch_guilds() to not get rate limited
	bot_guilds = (asyncio.run(ipc.request("get_guild_ids"))).response
	bot_guilds = literal_eval(bot_guilds)
	guilds_array = []

	for guild in guilds:
		if guild.permissions.administrator:
			print(guild.id)
			guild.status = True if guild.id in bot_guilds else False
			guilds_array.append(guild)

	guilds_array.sort(key=lambda x: x.status == False)
	return render_template("dashboard.html", guilds=guilds_array, user=user)

@app.route("/dashboard/server/<int:guild_id>", methods=['POST', 'GET'])
@requires_authorization
def server_view(guild_id):
	user = OAuth2.fetch_user()
	guild_obj = None
	for guild in OAuth2.fetch_guilds():
		if guild.id == guild_id:
			guild_obj = guild

	guild_name = asyncio.run(ipc.request("get_guild_name", guild_id=guild_id)).response
	if guild_name is None:
		return redirect(f'https://discord.com/oauth2/authorize?&client_id={app.config["DISCORD_CLIENT_ID"]}&scope=bot&permissions=8&guild_id={guild_id}&response_type=code&redirect_uri={app.config["DISCORD_REDIRECT_URI"]}')

	admin_bool = asyncio.run(ipc.request("check_admin", user_id=user.id, guild_id=guild_id))
	admin_bool = literal_eval(admin_bool.response)
	if admin_bool == True:
		pass
	elif admin_bool == False:
		return "Invalid permissions", 403
	else:
		return redirect(f'https://discord.com/oauth2/authorize?&client_id={app.config["DISCORD_CLIENT_ID"]}&scope=bot&permissions=8&guild_id={guild_id}&response_type=code&redirect_uri={app.config["DISCORD_REDIRECT_URI"]}')

	guild_channels = asyncio.run(ipc.request("get_guild_channels", guild_id=guild_id))
	conn, c = db.db_connect()
	if request.method == 'POST':
		log_channel = request.form["log_channel"]
		event_log_channel = request.form["event_log_channel"]
		print(guild_channels.response)
		if log_channel == 0 or log_channel in guild_channels.response:
			db.set_log_channel(guild_id, log_channel, conn, c)
		if event_log_channel == 0 or event_log_channel in guild_channels.response:
			db.set_event_log_channel(guild_id, event_log_channel, conn, c)
		db_log_channel = db.get_log_channel(guild_id, c)
		db_event_log_channel = db.get_event_log_channel(guild_id, c)
		conn.close()
		return render_template("server.html", guild=guild_obj, user=user, guild_channels=guild_channels.response, saved=True, log_channel=db_log_channel, event_log_channel=db_event_log_channel)
	else:
		db_log_channel = db.get_log_channel(guild_id, c)
		db_event_log_channel = db.get_event_log_channel(guild_id, c)
		conn.close()
		return render_template("server.html", guild=guild_obj, user=user, guild_channels=guild_channels.response, saved=False, log_channel=db_log_channel, event_log_channel=db_event_log_channel)

@app.route("/dashboard/server/<int:guild_id>/moderations/")
async def moderations_redirect(guild_id):
	return redirect(url_for('moderations', guild_id=guild_id, page_number=1))

@app.route("/dashboard/server/<int:guild_id>/moderations/page/<int:page_number>")
async def moderations(guild_id, page_number):
	user = None
	if OAuth2.authorized:
		user = OAuth2.fetch_user()

	guild_obj = None
	for guild in OAuth2.fetch_guilds():
		if guild.id == guild_id:
			guild_obj = guild
	conn, c = db.db_connect()
	page = 1
	total_pages = 0
	hero_chunk = None
	lock = False
	conn, c = db.db_connect()
	moderations = db.get_moderations_by_guild(guild_id, c)
	conn.close()
	try:
		for i in range(0, len(moderations), 12):
			chunk = moderations[i:i+12]
			total_pages = total_pages + 1
			if page == page_number and not lock:
				lock = True # so that it correctly paginates
				hero_chunk = []
				for moderation in chunk:
					mutable_moderation = list(moderation)
					mutable_moderation[2] = (await ipc.request("get_username", user_id=mutable_moderation[2])).response
					mutable_moderation[3] = (await ipc.request("get_username", user_id=mutable_moderation[3])).response
					mutable_moderation[7] = (datetime.fromtimestamp(float(moderation[7]))).strftime("%Y-%m-%d %H:%M:%S")
					if mutable_moderation[8] is None:
						mutable_moderation[8] = "N/A"
					if mutable_moderation[9] == 0:
						mutable_moderation[9] = "No"
					else:
						mutable_moderation[9] = "Yes"
					hero_chunk.append(tuple(mutable_moderation))
			elif lock:
				pass
			else:
				page = page + 1
	except Exception:
		return "Internal error", 403
	minimum_page = total_pages - (total_pages - 1)
	if minimum_page <= page <= total_pages:
		pass
	else:
		return "Invalid page", 403
	guild_name = (await ipc.request("get_guild_name", guild_id=guild_id)).response
	return render_template("moderations.html", user=user, guild_name=guild_name, guild_id=guild_id, chunk=hero_chunk, page=page, total_pages=total_pages, page_number=page_number)

if __name__ == '__main__':
	app.run(debug=True)