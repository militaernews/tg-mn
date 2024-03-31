import asyncio
import json
import logging
import os
import re
from datetime import datetime, timedelta

from pyrogram import Client, filters, compose, idle
from pyrogram.enums import ParseMode
from pyrogram.errors import MessageNotModified
from pyrogram.types import Message

import config
from data.lang import GERMAN, languages

from translation import debloat_text, format_text

from config import CHANNEL_BACKUP, CHANNEL_TEST
from data.db import get_source, get_source_ids_by_api_id, get_post, set_post, get_account
from model import Post

LOG_FILENAME = rf"./logs/{datetime.now().strftime('%Y-%m-%d')}/{datetime.now().strftime('%H-%M-%S')}.log"
os.makedirs(os.path.dirname(LOG_FILENAME), exist_ok=True)
logging.basicConfig(
    format="%(asctime)s %(levelname)-5s %(funcName)-20s [%(filename)s:%(lineno)d]: %(message)s",
    encoding="utf-8",
    filename=LOG_FILENAME,
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)


async def main():
    app = Client(
        name="Premium",
        api_id=config.API,
        api_hash=config.HASH,
        phone_number=config.NUMBER,
        parse_mode=ParseMode.HTML
    )

    bf = filters.channel & filters.chat(GERMAN.channel_id) & filters.incoming
    mf = bf & (filters.photo | filters.video | filters.animation)

    logging.info("-- STARTED // TG-MN  --")

    @app.on_message(

        filters.text & filters.regex(rf"^#{GERMAN.breaking}", re.IGNORECASE))  #bf &
    async def filter_messages(client, message):

        caption = re.sub(r'#\w+\s|\s{2,}', " ", message.text.html).strip()

        with open(r"./res/de/flags.json", "r", encoding="utf-8") as file:
            flag_names = json.load(file)

        hashtags = " #".join({flag_names[flag] for flag in flag_names if flag in caption})

        final_caption = f"🚨 #{GERMAN.breaking}\n\n{caption}\n\n#{hashtags}\n{GERMAN.footer}"
        await client.send_photo(chat_id=message.chat.id, photo="./res/de/breaking.png", caption=final_caption)

    @app.on_message(filters.text & bf)
    async def new_text(client: Client, message: Message):
        logging.info(f">>>>>> handle_text {message.chat.id, message.text.html}", )

        source = get_source(message.chat.id)

        text = await debloat_text(message, client)
        if not text:
            return

        logging.info(f"T X -single {text}", )

        text = format_text(text, message, source)

        if message.reply_to_message_id is not None:
            reply_post = get_post(message.chat.id, message.reply_to_message_id)
            if reply_post is None:
                reply_id = None
            else:
                reply_id = reply_post.message_id
        else:
            reply_id = None

        logging.info(f"send New Text {client.name}")
        msg = await client.send_message(source.destination, text, disable_web_page_preview=True)

        set_post(Post(
            msg.chat.id,
            msg.id,
            message.chat.id,
            message.forward_from_message_id,
            message.id,
            reply_id,
            text
        ))

    @app.on_edited_message(filters.text & bf)
    async def edit_text(client: Client, message: Message):
        logging.info(f">>>>>> edit_text {message.chat.id, message.text.html}", )

        if message.date < (datetime.now() - timedelta(weeks=1)):
            return

        await asyncio.sleep(60)
        post = get_post(message.chat.id, message.id)

        if post is None:
            await new_text(client, message)
            return

        source = get_source(message.chat.id)

        text = await debloat_text(message, client)
        if not text:
            return

        logging.info(f"edit text::: {post}", )

        text = format_text(text, message, source)
        try:
            await client.edit_message_text(post.destination, post.message_id, text, disable_web_page_preview=True)
        except MessageNotModified:
            pass

    @app.on_message(filters.media_group & filters.caption & mf)
    async def new_multiple(client: Client, message: Message):
        logging.info(f">>>>>> handle_multiple {message.chat.id, message.caption.html}", )

        source = get_source(message.chat.id)

        text = await debloat_text(message, client)
        if not text:
            return

        mg = await client.get_media_group(message.chat.id, message.id)

        text = format_text(text, message, source)

        if message.reply_to_message_id is not None:
            reply_post = get_post(message.chat.id, message.reply_to_message_id)
            if reply_post is None:
                reply_id = None
            else:
                reply_id = reply_post.message_id
        else:
            reply_id = None

        msgs = await client.copy_media_group(source.destination,
                                             from_chat_id=message.chat.id,
                                             message_id=message.id,
                                             captions=text)

        set_post(Post(
            msgs[0].chat.id,
            msgs[0].id,
            message.chat.id,
            message.forward_from_message_id,
            message.id,
            reply_id,
            text
        ))

    @app.on_message(filters.caption & mf)
    async def new_single(client: Client, message: Message):
        logging.info(f">>>>>> handle_single {message.chat.id}")

        source = get_source(message.chat.id)

        text = await debloat_text(message, client)
        if not text:
            return

        logging.info(f">>>>>> handle_single {source, message.chat.id}")
        text = format_text(text, message, source)

        if message.reply_to_message_id is not None:
            reply_post = get_post(message.chat.id, message.reply_to_message_id)
            if reply_post is None:
                reply_id = None

            else:
                reply_id = reply_post.message_id
        else:
            reply_id = None

        logging.info(f"---- new single {client.name}----- {source}")
        msg = await message.copy(source.destination, caption=text)  # media caption too long

        set_post(Post(
            msg.chat.id,
            msg.id,
            message.chat.id,
            message.forward_from_message_id,
            message.id,
            reply_id,
            text
        ))

        logging.info(f"----------------------------------------------------")

    #   logging.info(f">>>>>>>>>>>>>>>>>>>>> file_id ::::::::::::", message.photo.file_id)
    #  logging.info(f">>>>>>>>>>>>>>>>>>>>> file_unique_id ::::::::::::", message.photo.file_unique_id)

    @app.on_edited_message(filters.caption & mf)
    async def edit_caption(client: Client, message: Message):
        logging.info(f">>>>>> edit_caption {message.chat.id, message.caption.html}", )

        if message.date < (datetime.now() - timedelta(weeks=1)):
            return

        await asyncio.sleep(60)
        post = get_post(message.chat.id, message.id)

        if post is None:
            if message.media_group_id is None:
                await new_single(client, message)
            else:
                await new_multiple(client, message)
            return

        source = get_source(message.chat.id)

        text = await debloat_text(message, client)
        if not text:
            return

        text = format_text(text, message, source)

        try:
            logging.info(f"edit_caption ::::::::::::::::::::: {post}", )
            await client.edit_message_caption(post.destination, post.message_id, text)
        except MessageNotModified:
            pass

    try:
        print("RUN")
        await app.start()
        await idle()

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    asyncio.run(main())
