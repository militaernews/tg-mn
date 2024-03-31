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

from translation import format_text, translate

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

        for lang in languages:
            cap = format_text(translate(caption, 0, lang), lang)
            await client.send_photo(chat_id=message.chat.id, photo=f"./res/{lang.lang_key}/breaking.png", caption=cap)



    try:
        print("RUN")
        await app.start()
        await idle()

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    asyncio.run(main())
