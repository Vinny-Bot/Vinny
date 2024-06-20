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
						severity TEXT,
						time TEXT,
						duration INTEGER,
						active BOOLEAN
					)''')

	conn.commit()
	conn.close()

create_moderation_table()

def insert_moderation(guild_id: int, user_id: int, moderator_id: int, moderation_type: str, severity: str, time: str, duration: str):
	try:
		conn = sqlite3.connect(database)
		c = conn.cursor()
		
		# we increment the case/moderation id
		c.execute("SELECT MAX(moderation_id) AS max_id FROM moderations")
		result = c.fetchone()
		case_id = 1 if result[0] == None else result[0] + 1
		
		c.execute('''INSERT INTO moderations (moderation_id, guild_id, user_id, moderator_id, moderation_type, severity, time, duration, active)
					VALUES (?,?,?,?,?,?,?,?,?)''', (case_id, guild_id, user_id, moderator_id, moderation_type, severity, time, duration, True))
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
	c.execute("SELECT moderation_id, time, duration FROM moderations WHERE severity='S3' AND active=true")
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

def set_moderation_inactive(moderation_id):
	conn = sqlite3.connect(database)
	c = conn.cursor()
	c.execute('UPDATE moderations SET active=0 WHERE moderation_id=?', (moderation_id,))
	conn.commit()
	conn.close()