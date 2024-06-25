# viggy - discord moderation bot
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

import sqlite3
from pathlib import Path
from datetime import datetime
from utils import utils

database = Path(__file__).resolve().parent.parent.joinpath('moderation.db')

def create_moderation_table():
	conn = sqlite3.connect(database)
	c = conn.cursor()

	c.execute('''CREATE TABLE IF NOT EXISTS moderations (
						moderation_id INTEGER PRIMARY KEY AUTOINCREMENT,
						guild_id INTEGER,
						user_id INTEGER,
						moderator_id INTEGER,
						moderation_type TEXT,
						reason TEXT,
						severity TEXT,
						time TEXT,
						duration INTEGER,
		   				active BOOLEAN,
						tempban_active BOOLEAN
					)''')

	conn.commit()
	conn.close()

def create_guilds_table():
	conn = sqlite3.connect(database)
	c = conn.cursor()

	c.execute('''CREATE TABLE IF NOT EXISTS guilds (
					guild_id INTEGER PRIMARY KEY,
					log_channel_id INTEGER DEFAULT NULL,
					event_log_channel_id INTEGER DEFAULT NULL
				)''')

	conn.commit()
	conn.close()

create_guilds_table()
create_moderation_table()

def insert_moderation(guild_id: int, user_id: int, moderator_id: int, moderation_type: str, reason: str, severity: str, time: str, duration: str):
	try:
		conn = sqlite3.connect(database)
		c = conn.cursor()
		
		# we increment the case/moderation id
		c.execute("SELECT MAX(moderation_id) AS max_id FROM moderations")
		result = c.fetchone()
		case_id = 1 if result[0] == None else result[0] + 1
		
		c.execute('''INSERT INTO moderations (moderation_id, guild_id, user_id, moderator_id, moderation_type, reason, severity, time, duration, active, tempban_active)
					VALUES (?,?,?,?,?,?,?,?,?,?,?)''', (case_id, guild_id, user_id, moderator_id, moderation_type, reason, severity, time, duration, True, True))
		conn.commit()
		conn.close()
		return case_id
	except Exception as e:
		print(f"Error while inserting moderation: {e}")

def get_count_of_moderations():
	conn = sqlite3.connect(database)
	c = conn.cursor()
	c.execute("SELECT COUNT(*) FROM moderations")
	count = c.fetchone()[0]
	conn.close()
	return count

def get_active_tempbans(): # this gave me a headache, TLDR: checks for "active" tempbans
	conn = sqlite3.connect(database)
	c = conn.cursor()
	c.execute("SELECT moderation_id, time, duration FROM moderations WHERE severity='S3' AND tempban_active=true")
	results = []
	for row in c.fetchall():
		moderation_id = row[0]
		time_unix = float(row[1])
		duration_str = row[2]
		duration_td = utils.parse_duration(duration_str)
		time_obj = datetime.fromtimestamp(time_unix)
		updated_time = time_obj + duration_td # hooray, we now have a datetime object of when the user is supposed to be banned
		results.append({
			'moderation_id': moderation_id,
			'unban_time': updated_time
		})
	conn.close()
	return results # have fun with these, main.py! i know you'll make good use of these results

def get_moderation_by_id(moderation_id):
	conn = sqlite3.connect(database)
	c = conn.cursor()
	c.execute('SELECT * FROM moderations WHERE moderation_id=?', (moderation_id,))
	moderation = c.fetchone()
	conn.close()
	return moderation

def set_moderation_inactive_or_active(moderation_id, active: bool):
	conn = sqlite3.connect(database)
	c = conn.cursor()
	c.execute('UPDATE moderations SET active=0 WHERE moderation_id=?', (moderation_id,))
	conn.commit()
	conn.close()

def set_tempban_inactive(moderation_id):
	conn = sqlite3.connect(database)
	c = conn.cursor()
	c.execute('UPDATE moderations SET tempban_active=0 WHERE moderation_id=?', (moderation_id,))
	conn.commit()
	conn.close()

def set_log_channel(guild_id: int, channel_id: int):
	conn = sqlite3.connect(database)
	c = conn.cursor()
	c.execute('INSERT OR REPLACE INTO guilds (guild_id, log_channel_id, event_log_channel_id) VALUES (?, ?, ?)', (guild_id, channel_id, get_event_log_channel(guild_id)))
	conn.commit()
	conn.close()

def set_event_log_channel(guild_id: int, channel_id: int):
	conn = sqlite3.connect(database)
	c = conn.cursor()
	c.execute('INSERT OR REPLACE INTO guilds (guild_id, log_channel_id, event_log_channel_id) VALUES (?, ?, ?)', (guild_id, get_log_channel(guild_id), channel_id))
	conn.commit()
	conn.close()

def get_log_channel(guild_id: int) -> int:
	try:
		conn = sqlite3.connect(database)
		c = conn.cursor()
		c.execute('SELECT log_channel_id FROM guilds WHERE guild_id=?', (guild_id,))
		log_channel = c.fetchone()[0]
		conn.close()
		return log_channel
	except Exception:
		return 0

def get_event_log_channel(guild_id: int) -> int:
	try:
		conn = sqlite3.connect(database)
		c = conn.cursor()
		c.execute('SELECT event_log_channel_id FROM guilds WHERE guild_id=?', (guild_id,))
		log_channel = c.fetchone()[0]
		conn.close()
		return log_channel
	except Exception:
		return 0

def get_moderations_by_user_and_guild(guild_id: int, user_id: int, inactive: bool):
	conn = sqlite3.connect(database)
	c = conn.cursor()
	if not inactive:
		c.execute("SELECT * FROM moderations WHERE guild_id=? AND user_id=? AND active=1", (guild_id, user_id,))
	else:
		c.execute("SELECT * FROM moderations WHERE guild_id=? AND user_id=?", (guild_id, user_id,))
	moderations = c.fetchall()
	conn.close()
	return moderations