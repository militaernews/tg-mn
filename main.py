import asyncio
import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import Final

from pyrogram import Client, filters, compose, idle
from pyrogram.enums import ParseMode
from pyrogram.errors import MessageNotModified
from pyrogram.types import Message

import config
from data.lang import GERMAN, languages

from translation import format_text, translate

from config import CHANNEL_BACKUP, CHANNEL_TEST
from data.db import get_source, get_source_ids_by_api_id, get_post, set_post, get_account
from model import Post

LOG_FILENAME: Final[str] = rf"./logs/{datetime.now().strftime('%Y-%m-%d/%H-%M-%S')}.log"
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
    async def handle_breaking(client: Client, message: Message):
        await message.delete()

        final_caption = f"🚨 #{GERMAN.breaking}\n\n{format_text(message.text.html, GERMAN)}"
        msg = await client.send_photo(chat_id=message.chat.id, photo=f"./res/{GERMAN.lang_key}/breaking.png",
                                      caption=final_caption)

        for lang in languages:
            final_caption = f"🚨 #{lang.breaking}\n\n{format_text(translate(message.text.html, lang), lang)}"

            msg = await client.send_photo(chat_id=message.chat.id, photo=f"./res/{lang.lang_key}/breaking.png",
                                          caption=final_caption)

        # set_post(Post(   ))

    @app.on_message(bf & filters.media & filters.caption & ~filters.media_group)  # bf &
    async def handle_single(client: Client, message: Message):
        for lang in languages:
            final_caption = format_text(translate(message.caption.html, lang), lang)

            msg = await message.copy(chat_id=message.chat.id, caption=final_caption)

            #set_post(Post(   ))

        await message.edit_caption(format_text(message.caption.html, GERMAN))

    try:
        print("RUN")
        await app.start()
        await idle()

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    asyncio.run(main())
