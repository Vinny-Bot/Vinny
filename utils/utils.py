# pakmar - discord moderation bot
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