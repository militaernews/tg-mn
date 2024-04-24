from dataclasses import dataclass
from typing import Optional

from data.lang import MASTER


@dataclass
class Post:
    post_id: int
    lang: str = MASTER.lang_key
    msg_id: Optional[int] = None
    media_group_id: Optional[int] = None
    reply_id: Optional[int] = None
    file_type: Optional[int] = None
    file_id: Optional[str] = None
    text: Optional[str] = None


