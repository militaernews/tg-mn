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
