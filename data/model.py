import logging
from dataclasses import dataclass
from typing import Optional

from pyrogram.enums import MessageMediaType

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


def get_filetype(media: MessageMediaType) -> Optional[int]:
    if media == MessageMediaType.PHOTO:
        return 0
    if media == MessageMediaType.VIDEO:
        return 1
    if media == MessageMediaType.ANIMATION:
        return 2
    else:
        logging.error(f"Media {media} is not supported")
    return None
