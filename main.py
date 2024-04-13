import asyncio
import contextlib
import logging
import os
import re
import sys
from datetime import datetime

from pyrogram import Client, filters, idle
from pyrogram.enums import ParseMode
from pyrogram.errors import MessageNotModified
from pyrogram.types import Message

import config
from data.db import set_post, get_slave_post_ids, get_file_id, update_post_media
from data.lang import MASTER, SLAVES, SLAVE_DICT
from data.model import Post, get_filetype
from translation import format_text, translate
from utils import extract_file_id, get_input_media


def setup_logging():
    log_filename = f"./logs/{datetime.now().strftime('%Y-%m-%d/%H-%M-%S')}.log"
    os.makedirs(os.path.dirname(log_filename), exist_ok=True)
    logging.basicConfig(
        format="%(asctime)s %(levelname)-5s %(funcName)-20s [%(filename)s:%(lineno)d]: %(message)s",
        encoding="utf-8",
        filename=log_filename,
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def setup_event_loop_policy():
    if sys.version_info >= (3, 8) and sys.platform.lower().startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
    setup_logging()
    setup_event_loop_policy()

    app = Client(
        name="Premium",
        api_id=config.API,
        api_hash=config.HASH,
        phone_number=config.NUMBER,
        parse_mode=ParseMode.HTML
    )

    bf = filters.channel & filters.chat(MASTER.channel_id) & filters.incoming & ~filters.forwarded
    mf = bf & (filters.photo | filters.video | filters.animation)

    logging.info("-- STARTED // TG-MN  --")

    @app.on_message(
        bf &
        filters.text & filters.regex(rf"^#{MASTER.breaking}", re.IGNORECASE))
    async def handle_breaking(client: Client, message: Message):
        print(">>>>>> handle_breaking", message)
        await message.delete()

        # todo: what about supporting Breaking with images/videos supplied?

        master_caption = f"🚨 #{MASTER.breaking}\n\n{format_text(message.text.html)}"
        master_post = await client.send_photo(chat_id=message.chat.id, photo=f"./res/{MASTER.lang_key}/breaking.png",
                                              caption=master_caption)
        set_post(Post(master_post.id, MASTER.lang_key, master_post.id, file_type=get_filetype(master_post.media),
                      file_id=master_post.photo.file_id))

        for lang in SLAVES:
            translated_caption = f"🚨 #{lang.breaking}\n\n{format_text(translate(message.text.html, lang), lang)}"
            slave_post = await client.send_photo(chat_id=lang.channel_id, photo=f"./res/{lang.lang_key}/breaking.png",
                                                 caption=translated_caption)
            set_post(Post(master_post.id, lang.lang_key, slave_post.id, file_type=get_filetype(slave_post.media),
                          file_id=slave_post.photo.file_id))

    @app.on_message(
        bf &
        filters.text & filters.regex(rf"^#{MASTER.announce}", re.IGNORECASE))
    async def handle_announce(client: Client, message: Message):
        print(">>>>>> handle_announce", message)
        await message.delete()

        # todo: what about supporting Breaking with images/videos supplied?

        master_caption = f"🚨 #{MASTER.announce}\n\n{format_text(message.text.html)}"
        master_post = await client.send_photo(chat_id=message.chat.id, photo=f"./res/{MASTER.lang_key}/announce.png",
                                              caption=master_caption)
        set_post(Post(master_post.id, MASTER.lang_key, master_post.id, file_type=get_filetype(master_post.media),
                      file_id=master_post.photo.file_id))

        for lang in SLAVES:
            translated_caption = f"🚨 #{lang.announce}\n\n{format_text(translate(message.text.html, lang), lang)}"
            slave_post = await client.send_photo(chat_id=lang.channel_id, photo=f"./res/{lang.lang_key}/announce.png",
                                                 caption=translated_caption)
            set_post(Post(master_post.id, lang.lang_key, slave_post.id, file_type=get_filetype(slave_post.media),
                          file_id=slave_post.photo.file_id))

    @app.on_edited_message(bf & filters.caption)
    # fixme: does incoming work for edited??
    # filters.caption & filters.incoming
    async def handle_edited_media_caption(client: Client, message: Message):
        print(">>>>>> handle_edited_media_caption", message)
        caption_changed = MASTER.footer not in message.caption.html
        # todo: and also compare with db entry
        if caption_changed:
            with contextlib.suppress(MessageNotModified):
                await message.edit_caption(format_text(message.caption.html))
                print("editing MASTER")

        for lang_key, slave_post_id in get_slave_post_ids(message.id).items():
            lang = SLAVE_DICT[lang_key]
            old_file_id = get_file_id(lang.lang_key, slave_post_id)
            new_file_id = extract_file_id(message)

            if caption_changed:
                translated_caption = format_text(translate(message.caption.html, lang), lang)

                if new_file_id == old_file_id:
                    print("editing SLAVE caption")
                    return await client.edit_message_caption(chat_id=lang.channel_id, message_id=slave_post_id,
                                                             caption=translated_caption)
            else:
                translated_caption = None

            with contextlib.suppress(MessageNotModified):
                slave_post = await client.edit_message_media(chat_id=lang.channel_id, message_id=slave_post_id,
                                                             media=get_input_media(message, translated_caption))
                update_post_media(lang_key, slave_post_id, get_filetype(slave_post.media), extract_file_id(slave_post))
                print("editing SLAVE media", slave_post)

    @app.on_edited_message(bf & mf & ~filters.caption)
    async def handle_edited_media(client: Client, message: Message):
        print(">>>>>> handle_edited_media", message)

        print("slave ids: ", get_slave_post_ids(message.id))

        for lang_key, slave_post_id in get_slave_post_ids(message.id).items():
            lang = SLAVE_DICT[lang_key]
            old_file_id = get_file_id(lang.lang_key, slave_post_id)
            new_file_id = extract_file_id(message)

            print(lang.lang_key, old_file_id, new_file_id)

            if old_file_id == new_file_id:
                continue

            print("editing SLAVE media")
            with contextlib.suppress(MessageNotModified):
                slave_post = await client.edit_message_media(chat_id=lang.channel_id, message_id=slave_post_id,
                                                             media=get_input_media(message))
                update_post_media(lang_key, slave_post_id, get_filetype(slave_post.media), extract_file_id(slave_post))

    @app.on_message(bf & mf & filters.caption & ~filters.media_group)
    async def handle_single(client: Client, message: Message):
        print(">>>>>> handle_single", message)

        slave_replies = {}
        if message.reply_to_message_id is not None:
            slave_replies = get_slave_post_ids(message.reply_to_message_id)

        for slave in SLAVES:
            final_caption = format_text(translate(message.caption.html, slave), slave)
            reply_id = slave_replies.get(slave.lang_key, None)

            slave_post = await message.copy(chat_id=slave.channel_id, caption=final_caption,
                                            reply_to_message_id=reply_id)
            set_post(Post(message.id, slave.lang_key, slave_post.id, file_type=get_filetype(slave_post.media),
                          file_id=slave_post.photo.file_id, reply_id=reply_id), )

        with contextlib.suppress(MessageNotModified):
            await message.edit_caption(format_text(message.caption.html, MASTER))
        set_post(Post(message.id, MASTER.lang_key, message.id, file_type=get_filetype(message.media),
                      file_id=extract_file_id(message), reply_id=message.reply_to_message_id))

    @app.on_message(bf & mf & filters.caption & filters.media_group)
    async def handle_multiple(client: Client, message: Message):
        print(">>>>>> handle_multiple", message)

        mg = await message.get_media_group()

        slave_replies = {}
        if message.reply_to_message_id is not None:
            slave_replies = get_slave_post_ids(message.reply_to_message_id)

        for slave in SLAVES:
            final_caption = format_text(translate(message.caption.html, slave), slave)
            reply_id = slave_replies.get(slave.lang_key, None)

            slave_posts = await client.copy_media_group(slave.channel_id, MASTER.channel_id, message.id, final_caption,
                                                        reply_to_message_id=reply_id)

            for index, slave_post in enumerate(slave_posts):
                print("slave_post: ", slave_post.id, slave.lang_key)
                set_post(Post(mg[index].id, slave.lang_key, slave_post.id, file_type=get_filetype(slave_post.media),
                              file_id=extract_file_id(slave_post), reply_id=reply_id))

        print("master_post: ", message.id),
        with contextlib.suppress(MessageNotModified):
            await message.edit_caption(format_text(message.caption.html, MASTER))
        for member in mg:
            print("master_post-member: ", member.id),
            set_post(Post(member.id, MASTER.lang_key, member.id, file_type=get_filetype(member.media),
                          file_id=extract_file_id(member), reply_id=message.reply_to_message_id,
                          media_group_id=message.media_group_id))

    @app.on_message(bf & filters.text)
    async def handle_text(client: Client, message: Message):
        print(">>>>>> handle_text", message)

        slave_replies = {}
        if message.reply_to_message_id is not None:
            slave_replies = get_slave_post_ids(message.reply_to_message_id)

        for slave in SLAVES:
            translated_text = format_text(translate(message.text.html, slave), slave)
            reply_id = slave_replies.get(slave.lang_key, None)
            slave_post = await client.send_message(
                chat_id=slave.channel_id,
                text=translated_text,
                reply_to_message_id=reply_id
            )
            set_post(Post(message.id, slave.lang_key, slave_post.id, reply_id=slave_post.reply_to_message_id))

        with contextlib.suppress(MessageNotModified):
            await message.edit_text(format_text(message.text.html, MASTER))
        set_post(Post(message.id, MASTER.lang_key, message.id, reply_id=message.reply_to_message_id))

    @app.on_edited_message(bf & filters.text)
    # fixme: does incoming work for edited??
    async def handle_edited_text(client: Client, message: Message):
        print(">>>>>> handle_edited_text", message)
        if MASTER.footer in message.text.html:
            return
        # todo: and also compare with db entry

        print("editing MASTER text")
        with contextlib.suppress(MessageNotModified):
            await message.edit_text(format_text(message.text.html))

        for lang_key, slave_post_id in get_slave_post_ids(message.id).items():
            lang = SLAVE_DICT[lang_key]
            translated_text = format_text(translate(message.text.html, lang), lang)

            print("editing SLAVE text")
            with contextlib.suppress(MessageNotModified):
                slave_post = await client.edit_message_text(chat_id=lang.channel_id, message_id=slave_post_id,
                                                            text=translated_text)
            print(slave_post)

    await app.start()
    print("RUN")
    await idle()


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
