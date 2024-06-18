import sqlite3
from pathlib import Path

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
						duration INTEGER
					)''')

	conn.commit()
	conn.close()

create_moderation_table()

def insert_moderation(guild_id: int, user_id: int, moderator_id: int, moderation_type: str, severity: str, time: str, duration: str):
	print("Los gringos")
	try:
		print("Gringo")
		conn = sqlite3.connect(database)
		c = conn.cursor()
		
		# we increment the case/moderation id
		c.execute("SELECT MAX(moderation_id) AS max_id FROM moderations")
		result = c.fetchone()
		case_id = 1 if result[0] == None else result[0] + 1
		print(case_id)
		print("Casablanca")
		
		c.execute('''INSERT INTO moderations (moderation_id, guild_id, user_id, moderator_id, moderation_type, severity, time, duration)
					VALUES (?,?,?,?,?,?,?,?)''', (case_id, guild_id, user_id, moderator_id, moderation_type, severity, time, duration))
		print("SIUU")
		conn.commit()
		print("Pendu")
		conn.close()
		return case_id
	except Exception as e:
		print("Error: ", e)

def get_count_of_moderations():
	conn = sqlite3.connect(database)
	c = conn.cursor()
	c.execute("SELECT COUNT(*) FROM moderations")
	count = c.fetchone()[0]
	conn.close()
	return count