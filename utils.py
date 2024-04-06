from pyrogram.types import Message, InputMedia, InputMediaPhoto, InputMediaVideo, InputMediaAnimation


def get_file_id(message: Message) -> str:
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
