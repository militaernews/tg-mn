import logging
from typing import Optional

from pyrogram.enums import MessageMediaType
from pyrogram.types import Message, InputMedia, InputMediaPhoto, InputMediaVideo, InputMediaAnimation


def extract_file_id(message: Message) -> str:
    if message.photo:
        return message.photo.file_id
    elif message.video:
        return message.video.file_id
    elif message.animation:
        return message.animation.file_id


def get_input_media(message: Message, caption: str = None) -> InputMedia:
    if message.photo:
        return InputMediaPhoto(message.photo.file_id, caption=caption)
    elif message.video:
        return InputMediaVideo(message.video.file_id, caption=caption)
    elif message.animation:
        return InputMediaAnimation(message.animation.file_id, caption=caption)


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
