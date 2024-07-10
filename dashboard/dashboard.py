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
from flask import Flask, render_template, redirect, request, url_for, abort
from flask_discord import DiscordOAuth2Session, requires_authorization, Unauthorized, models
from discord.ext.ipc import Client
from discord import Guild
import sys
import os
sys.path.append(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')))
from utils import utils, db, info
from ast import literal_eval

dashboard_version = "1.2.6"
cached_usernames = {}

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

@app.errorhandler(404)
def page_not_found(error):
	user = None
	if OAuth2.authorized:
		user = OAuth2.fetch_user()
	return render_template('html_error.html', user=user, error="404", error_message="Resource not found", title="404 Not found", description="404 Not found"), 404

@app.errorhandler(401)
def page_not_found(error):
	user = None
	if OAuth2.authorized:
		user = OAuth2.fetch_user()
	return render_template('html_error.html', user=user, error="403", error_message="Unauthorized", title="401 Unauthorized", description="401 Unauthorized"), 401

@app.errorhandler(403)
def page_not_found(error):
	user = None
	if OAuth2.authorized:
		user = OAuth2.fetch_user()
	return render_template('html_error.html', user=user, error="403", error_message="Forbidden", title="403 Forbidden", description="403 Forbidden"), 403

@app.errorhandler(500)
def page_not_found(error):
	user = None
	if OAuth2.authorized:
		user = OAuth2.fetch_user()
	return render_template('html_error.html', user=user, error="500", error_message="Internal server error", title="500 Internal server error", description="401 Internal server error"), 403

@app.route('/')
def index():
	user = None
	if OAuth2.authorized:
		user = OAuth2.fetch_user()
	return render_template('index.html', user=user, authorized=OAuth2.authorized, title=f"Homepage", description=f"Welcome to Vinny! A free and open-source moderation bot based on sanctions", url=f"{config_data['dashboard']['url']}{url_for('index')}")

@app.route('/learnmore')
def learnmore():
	user = None
	if OAuth2.authorized:
		user = OAuth2.fetch_user()
	return render_template('learnmore.html', user=user, authorized=OAuth2.authorized, title=f"Learn More", description=f"Learn more about Vinny", url=f"{config_data['dashboard']['url']}{url_for('learnmore')}")

@app.route('/privacypolicy')
def privacypolicy():
	user = None
	if OAuth2.authorized:
		user = OAuth2.fetch_user()
	return render_template('privacypolicy.html', user=user, authorized=OAuth2.authorized, title=f"Privacy Policy", description=f"Vinny privacy policy", url=f"{config_data['dashboard']['url']}{url_for('privacypolicy')}")

@app.context_processor
def inject_global_vars():
	return {'dashboard_version': dashboard_version, 'version': info.get_vinny_version()}

@app.route("/login/")
def login():
	return OAuth2.create_session(scope=["identify", "guilds"])

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
			guild.status = True if guild.id in bot_guilds else False
			guilds_array.append(guild)

	guilds_array.sort(key=lambda x: x.status == False)
	return render_template("dashboard.html", guilds=guilds_array, user=user, title=f"Dashboard", description=f"View all available servers", url=f"{config_data['dashboard']['url']}{url_for('dashboard')}")

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
	c.execute("INSERT OR IGNORE INTO guilds (guild_id) VALUES (?)", (guild_id,))
	conn.commit()
	if request.method == 'POST':
		form_fields = {
			"log_channel_id": request.form["log_channel"],
			"event_log_channel_id": request.form["event_log_channel"],
			"nonce_filter": int(request.form["nonce_filter"]),
			"bot_filter": int(request.form["bot_filter"]),
			"on_message_delete": int(request.form["on_message_delete"]),
			"on_message_edit": int(request.form["on_message_edit"]),
			"on_member_join": int(request.form["on_member_join"]),
			"on_member_leave": int(request.form["on_member_leave"]),
			"on_member_update": int(request.form["on_member_update"]),
			"on_guild_channel_create": int(request.form["on_guild_channel_create"]),
			"on_guild_channel_delete": int(request.form["on_guild_channel_delete"])
		}
		for form in form_fields:
			if form_fields[form] == 0 or form_fields[form] == 1 or form_fields[form] in guild_channels.response:
				db.set_config_value(guild_id, form, form_fields[form], conn, c)
		db_values = {}
		defaults = {
			"log_channel_id": 0,
			"event_log_channel_id": 0,
			"nonce_filter": 0,
			"bot_filter": 0,
			"on_message_delete": 1,
			"on_message_edit": 1,
			"on_member_join": 1,
			"on_member_leave": 1,
			"on_member_update": 1,
			"on_guild_channel_create": 1,
			"on_guild_channel_delete": 1,
		}
		for key in defaults:
			db_values[f"{key}"] = db.get_config_value(guild_id, key, c, defaults[f"{key}"])
		conn.close()
		return render_template("server.html", guild=guild_obj, user=user, guild_channels=guild_channels.response, saved=True, db_values=db_values, title=f"{guild_name}", description=f"{guild_name} configuration panel", url=f"{config_data['dashboard']['url']}{url_for('server_view', guild_id=guild_id)}")
	else:
		db_values = {}
		defaults = {
			"log_channel_id": 0,
			"event_log_channel_id": 0,
			"nonce_filter": 0,
			"bot_filter": 0,
			"on_message_delete": 1,
			"on_message_edit": 1,
			"on_member_join": 1,
			"on_member_leave": 1,
			"on_member_update": 1,
			"on_guild_channel_create": 1,
			"on_guild_channel_delete": 1,
		}
		for key in defaults:
			db_values[f"{key}"] = db.get_config_value(guild_id, key, c, defaults[f"{key}"])
		conn.close()
		return render_template("server.html", guild=guild_obj, user=user, guild_channels=guild_channels.response, saved=False, db_values=db_values, title=f"{guild_name}", description=f"{guild_name} configuration panel", url=f"{config_data['dashboard']['url']}{url_for('server_view', guild_id=guild_id)}")

@app.route("/dashboard/server/<int:guild_id>/moderations/")
async def moderations_redirect(guild_id):
	return redirect(url_for('moderations', guild_id=guild_id, page_number=1))

@app.route("/dashboard/server/<int:guild_id>/moderations/page/<int:page_number>")
async def moderations(guild_id, page_number):
	user = None
	if OAuth2.authorized:
		user = OAuth2.fetch_user()

	conn, c = db.db_connect()
	page = 1
	total_pages = 0
	hero_chunk = None
	lock = False
	conn, c = db.db_connect()
	moderations = db.get_moderations_by_guild(guild_id, c)
	conn.close()
	try:
		order = request.args.get('order', default='newest', type=str)
		show_inactive = request.args.get('show_inactive', default='false', type=str)
		if order == "newest":
			moderations.reverse()
		for i in range(0, len(moderations), 12):
			chunk = moderations[i:i+12]
			total_pages += 1
			if page == page_number and not lock:
				lock = True # so that it correctly paginates
				hero_chunk = []
				for moderation in chunk:
					mutable_moderation = list(moderation)
					if moderation[2] not in cached_usernames:	
						mutable_moderation[2] = (await ipc.request("get_username", user_id=mutable_moderation[2])).response
						cached_usernames.update({moderation[2]: mutable_moderation[2]})
					else:
						mutable_moderation[2] = cached_usernames[moderation[2]]
					if moderation[3] not in cached_usernames:	
						mutable_moderation[3] = (await ipc.request("get_username", user_id=mutable_moderation[3])).response
						cached_usernames.update({moderation[3]: mutable_moderation[3]})
					else:
						mutable_moderation[3] = cached_usernames[moderation[3]]
					mutable_moderation[7] = (datetime.fromtimestamp(float(moderation[7]))).strftime("%Y-%m-%d %H:%M:%S")
					if mutable_moderation[8] is None or mutable_moderation[8] == "N/A":
						mutable_moderation[8] = ""
					if mutable_moderation[9] == 0:
						mutable_moderation[9] = "No"
					else:
						mutable_moderation[9] = "Yes"
					mutable_moderation.append(moderation[2])
					mutable_moderation.append(moderation[3])
					if mutable_moderation[9] == "Yes":
						hero_chunk.append(tuple(mutable_moderation))
					elif mutable_moderation[9] == "No" and show_inactive == "true":
						hero_chunk.append(tuple(mutable_moderation))
			elif lock:
				pass
			else:
				page += 1
	except Exception:
		abort(500)
	guild_name = (await ipc.request("get_guild_name", guild_id=guild_id)).response
	if guild_name is None:
		abort(403)
	if hero_chunk is None and page_number == 1:
		return render_template('html_error.html', user=user, error="404", error_message="No moderations found for this server", title="404 Not found", description="404 Not found"), 404
	minimum_page = total_pages - (total_pages - 1)
	if minimum_page <= page <= total_pages:
		pass
	else:
		abort(404)

	return render_template("moderations.html", user=user, guild_name=guild_name, guild_id=guild_id, chunk=hero_chunk, page=page, total_pages=total_pages, page_number=page_number, title=f"Moderations - {guild_name}", description=f"View all moderations in {guild_name}", url=f"{config_data['dashboard']['url']}{url_for('moderations', guild_id=guild_id, page_number=1)}", order=order, show_inactive=show_inactive)

if __name__ == '__main__':
	app.run()