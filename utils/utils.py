import re
import datetime

def parse_duration(duration_str): # convert 1m, 1h, 1d, etc to seconds and then to a timedelta
	pattern = r"(\d+)([mh]?)"
	match = re.search(pattern, duration_str)
	if match:
		num, unit = match.groups()
		if unit == 's':
			factor = 1
		elif unit == 'm':
			factor = 60
		elif unit == 'h':
			factor = 3600
		elif unit == 'd':
			factor = 86400
		else:
			factor = 1
		
		total_seconds = float(num) * factor
		
		return datetime.timedelta(seconds=total_seconds)
	else:
		raise ValueError(f"Invalid duration format: {duration_str}")