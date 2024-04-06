import asyncio
import logging
import os
import re
from datetime import datetime
from typing import Final

from pyrogram import Client, filters, idle
from pyrogram.enums import ParseMode
from pyrogram.types import Message

import config
from data.db import set_post, get_posts
from data.lang import slaves, MASTER
from data.model import Post, get_filetype
from translation import format_text, translate

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

    bf = filters.channel & filters.chat(MASTER.channel_id) & filters.incoming
    mf = bf & (filters.photo | filters.video | filters.animation)

    logging.info("-- STARTED // TG-MN  --")

    @app.on_message(

        filters.text & filters.regex(rf"^#{MASTER.breaking}", re.IGNORECASE))  #bf &
    async def handle_breaking(client: Client, message: Message):
        await message.delete()

        #todo: what about supporting Breaking with images/videos supplied?
        # todo: replace LI with actual lang keys

        master_caption = f"🚨 #{MASTER.breaking}\n\n{format_text(message.text.html, MASTER)}"
        master_post = await client.send_photo(chat_id=message.chat.id, photo=f"./res/{MASTER.lang_key}/breaking.png",
                                              caption=master_caption)
        set_post(Post(master_post.id, "li", master_post.id, file_type=get_filetype(master_post.media),
                      file_id=master_post.photo.file_id))

        for lang in slaves:
            translated_caption = f"🚨 #{lang.breaking}\n\n{format_text(translate(message.text.html, lang), lang)}"
            slave_post = await client.send_photo(chat_id=message.chat.id, photo=f"./res/{lang.lang_key}/breaking.png",
                                                 caption=translated_caption)
            set_post(Post(master_post.id, "li", slave_post.id, file_type=get_filetype(slave_post.media),
                          file_id=slave_post.photo.file_id))

    @app.on_edited_message(filters.photo  & filters.caption)

 # bf &
    async def handle_edit(client: Client, message: Message):
#todo: edit media
        await message.edit_caption(format_text(message.caption.html, MASTER))

        for lang_key, slave_post_id in get_posts(message.id).items():

        for lang in slaves:
            translated_caption = f"🚨 #{lang.breaking}\n\n{format_text(translate(message.text.html, lang), lang)}"

            
            slave_post = await client.edit_message_caption(chat_id=message.chat.id,
                                                           caption=translated_caption)
            print(slave_post)





    @app.on_message(bf & filters.media & filters.caption & ~filters.media_group)  # bf &
    async def handle_single(client: Client, message: Message):
        for slave in slaves.items():
            final_caption = format_text(translate(message.caption.html, slave), slave)

            msg = await message.copy(chat_id=message.chat.id, caption=final_caption)

            # set_post(Post())

        await message.edit_caption(format_text(message.caption.html, MASTER))

    try:
        print("RUN")
        await app.start()
        await idle()

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    asyncio.run(main())
