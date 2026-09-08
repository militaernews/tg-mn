import json
import os
from typing import Final, List

from dotenv import load_dotenv

load_dotenv()



DEEPL = json.loads(os.getenv('DEEPL'))
DATABASE_URL = os.getenv("DATABASE_URL")

HASH = os.getenv("TG_HASH")
API = os.getenv("TG_ID")
NUMBER = os.getenv("TG_NUMBER")
ADMINS: Final[List[str]] = json.loads(os.getenv('ADMINS'))

# Scheduling rules for handing queued_posts (from ptb-suggest's /synthesize)
# off to Telegram's own native message scheduling in the MASTER channel.
SCHEDULE_MIN_GAP_MINUTES: Final[int] = int(os.getenv('SCHEDULE_MIN_GAP_MINUTES', 30))
SCHEDULE_QUIET_START_HOUR: Final[int] = int(os.getenv('SCHEDULE_QUIET_START_HOUR', 20))  # no new posts from here...
SCHEDULE_QUIET_END_HOUR: Final[int] = int(os.getenv('SCHEDULE_QUIET_END_HOUR', 7))  # ...until here (local time)
SCHEDULE_TIMEZONE: Final[str] = os.getenv('SCHEDULE_TIMEZONE', 'Europe/Berlin')
SCHEDULE_POLL_INTERVAL_SECONDS: Final[int] = int(os.getenv('SCHEDULE_POLL_INTERVAL_SECONDS', 120))
