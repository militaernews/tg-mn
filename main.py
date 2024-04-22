import contextlib
import logging
import os
import re
import sys
from asyncio import sleep, run, set_event_loop_policy, WindowsSelectorEventLoopPolicy
from datetime import datetime
from typing import List

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
        set_event_loop_policy(WindowsSelectorEventLoopPolicy())


async def main():
    app = Client(
        name="Premium",
        api_id=config.API,
        api_hash=config.HASH,
        phone_number=config.NUMBER,
        parse_mode=ParseMode.HTML
    )

    bf = filters.channel & filters.chat(MASTER.channel_id) & filters.incoming & ~filters.forwarded & ~filters.scheduled
    mf = bf & (filters.photo | filters.video | filters.animation)

    logging.info("-- STARTED // TG-MN  --")

    @app.on_message(
        bf &
        filters.text & filters.regex(rf"^#{MASTER.breaking}", re.IGNORECASE))
    async def handle_breaking(client: Client, message: Message):
        logging.info(f">>>>>> handle_breaking: {message}", )
        await message.delete()

        # todo: what about supporting Breaking with images/videos supplied?

        master_caption = f"🚨 #{MASTER.breaking}\n\n{format_text(message.text.html)}"
        master_post = await client.send_photo(chat_id=message.chat.id, photo=f"./res/{MASTER.lang_key}/breaking.png",
                                              caption=master_caption)
        await set_post(Post(master_post.id, MASTER.lang_key, master_post.id, file_type=get_filetype(master_post.media),
                            file_id=master_post.photo.file_id))

        for lang in SLAVES:
            translated_caption = f"🚨 #{lang.breaking}\n\n{format_text(translate(message.text.html, lang), lang)}"
            slave_post = await client.send_photo(chat_id=lang.channel_id, photo=f"./res/{lang.lang_key}/breaking.png",
                                                 caption=translated_caption)
            await set_post(Post(master_post.id, lang.lang_key, slave_post.id, file_type=get_filetype(slave_post.media),
                                file_id=slave_post.photo.file_id))

    @app.on_message(
        bf &
        filters.text & filters.regex(rf"^#{MASTER.announce}", re.IGNORECASE))
    async def handle_announce(client: Client, message: Message):
        logging.info(f">>>>>> handle_announce: {message}", )
        await message.delete()

        # todo: what about supporting Breaking with images/videos supplied?

        master_caption = f"📢 #{MASTER.announce}\n\n{format_text(message.text.html)}"
        master_post = await client.send_photo(chat_id=message.chat.id, photo=f"./res/{MASTER.lang_key}/announce.png",
                                              caption=master_caption)
        await set_post(Post(master_post.id, MASTER.lang_key, master_post.id, file_type=get_filetype(master_post.media),
                            file_id=master_post.photo.file_id))

        for lang in SLAVES:
            translated_caption = f"📢 #{lang.announce}\n\n{format_text(translate(message.text.html, lang), lang)}"
            slave_post = await client.send_photo(chat_id=lang.channel_id, photo=f"./res/{lang.lang_key}/announce.png",
                                                 caption=translated_caption)
            await set_post(Post(master_post.id, lang.lang_key, slave_post.id, file_type=get_filetype(slave_post.media),
                                file_id=slave_post.photo.file_id))

    @app.on_message(mf & filters.caption & ~filters.media_group)
    async def handle_single(client: Client, message: Message):
        logging.info(f">>>>>> handle_single: {message}", )

        slave_replies = {}
        if message.reply_to_message_id is not None:
            slave_replies = await get_slave_post_ids(message.reply_to_message_id)

        for slave in SLAVES:
            final_caption = format_text(translate(message.caption.html, slave), slave)
            reply_id = slave_replies.get(slave.lang_key, None)

            slave_post = await message.copy(chat_id=slave.channel_id, caption=final_caption,
                                            reply_to_message_id=reply_id)
            await set_post(Post(message.id, slave.lang_key, slave_post.id, file_type=get_filetype(slave_post.media),
                                file_id=slave_post.photo.file_id, reply_id=reply_id), )

        with contextlib.suppress(MessageNotModified):
            await message.edit_caption(format_text(message.caption.html, MASTER))
        await set_post(Post(message.id, MASTER.lang_key, message.id, file_type=get_filetype(message.media),
                            file_id=extract_file_id(message), reply_id=message.reply_to_message_id))

    @app.on_message(mf & filters.caption & filters.media_group)
    async def handle_multiple(client: Client, message: Message):
        logging.info(f">>>>>> handle_multiple: {message}", )

        await sleep(3)
        mg = await message.get_media_group()

        logging.info(f"MG: {mg}", )

        slave_replies = {}
        if message.reply_to_message_id is not None:
            slave_replies = await get_slave_post_ids(message.reply_to_message_id)

        for slave in SLAVES:
            final_caption = format_text(translate(message.caption.html, slave), slave)
            reply_id = slave_replies.get(slave.lang_key, None)

            slave_posts = await client.copy_media_group(slave.channel_id, MASTER.channel_id, message.id, final_caption,
                                                        reply_to_message_id=reply_id)

            for index, slave_post in enumerate(slave_posts):
                logging.info(f"slave_post: {slave_post.id} - {slave.lang_key}")
                await set_post(
                    Post(mg[index].id, slave.lang_key, slave_post.id, file_type=get_filetype(slave_post.media),
                         file_id=extract_file_id(slave_post), reply_id=reply_id))

        logging.info(f"master_post: {message.id}"),
        with contextlib.suppress(MessageNotModified):
            await message.edit_caption(format_text(message.caption.html, MASTER))
        for member in mg:
            logging.info(f"master_post-member: {member.id}", )
            await set_post(Post(member.id, MASTER.lang_key, member.id, file_type=get_filetype(member.media),
                                file_id=extract_file_id(member), reply_id=message.reply_to_message_id,
                                media_group_id=message.media_group_id))

    @app.on_message(bf & filters.text)
    async def handle_text(client: Client, message: Message):
        logging.info(f">>>>>> handle_text: {message}", )

        slave_replies = {}
        if message.reply_to_message_id is not None:
            slave_replies = await get_slave_post_ids(message.reply_to_message_id)

        for slave in SLAVES:
            translated_text = format_text(translate(message.text.html, slave), slave)
            reply_id = slave_replies.get(slave.lang_key, None)
            slave_post = await client.send_message(
                chat_id=slave.channel_id,
                text=translated_text,
                reply_to_message_id=reply_id
            )
            await set_post(Post(message.id, slave.lang_key, slave_post.id, reply_id=slave_post.reply_to_message_id))

        with contextlib.suppress(MessageNotModified):
            await message.edit_text(format_text(message.text.html, MASTER))
        await set_post(Post(message.id, MASTER.lang_key, message.id, reply_id=message.reply_to_message_id))

    @app.on_edited_message(bf & filters.caption)
    # fixme: does incoming work for edited??
    # filters.caption & filters.incoming
    async def handle_edited_media_caption(client: Client, message: Message):
        await sleep(5)
        logging.info(f">>>>>> handle_edited_media_caption: {message}", )
        caption_changed = MASTER.footer not in message.caption.html
        # todo: and also compare with db entry
        if caption_changed:
            with contextlib.suppress(MessageNotModified):
                await message.edit_caption(format_text(message.caption.html))
                logging.info("editing MASTER")

        slave_posts = await get_slave_post_ids(message.id)
        if slave_posts is None:
            return

        for lang_key, slave_post_id in slave_posts.items():
            lang = SLAVE_DICT[lang_key]
            old_file_id = await get_file_id(lang.lang_key, slave_post_id)
            new_file_id = extract_file_id(message)

            if caption_changed:
                translated_caption = format_text(translate(message.caption.html, lang), lang)

                if new_file_id == old_file_id:
                    logging.info("editing SLAVE caption")
                    return await client.edit_message_caption(chat_id=lang.channel_id, message_id=slave_post_id,
                                                             caption=translated_caption)
            else:
                translated_caption = None

            with contextlib.suppress(MessageNotModified):
                slave_post = await client.edit_message_media(chat_id=lang.channel_id, message_id=slave_post_id,
                                                             media=get_input_media(message, translated_caption))
                await update_post_media(lang_key, slave_post_id, get_filetype(slave_post.media),
                                        extract_file_id(slave_post))
                logging.info(f"editing SLAVE media: {slave_post}", )

    @app.on_edited_message(mf & ~filters.caption)
    async def handle_edited_media(client: Client, message: Message):
        await sleep(5)
        logging.info(f">>>>>> handle_edited_media: {message}", )

        slaves = await get_slave_post_ids(message.id)
        if len(slaves) == 0:
            return
        logging.info(f"slave ids: {slaves}", )

        for lang_key, slave_post_id in slaves.items():
            lang = SLAVE_DICT[lang_key]
            old_file_id = await get_file_id(lang.lang_key, slave_post_id)
            new_file_id = extract_file_id(message)

            logging.info(f"slave {lang.lang_key} old: {old_file_id} new: {new_file_id}")
            if old_file_id == new_file_id:
                continue

            logging.info("editing SLAVE media")
            with contextlib.suppress(MessageNotModified):
                slave_post = await client.edit_message_media(chat_id=lang.channel_id, message_id=slave_post_id,
                                                             media=get_input_media(message))
                await update_post_media(lang_key, slave_post_id, get_filetype(slave_post.media),
                                        extract_file_id(slave_post))

    @app.on_edited_message(bf & filters.text)
    # fixme: does incoming work for edited??
    async def handle_edited_text(client: Client, message: Message):
        await sleep(5)
        logging.info(f">>>>>> handle_edited_text: {message}", )
        if MASTER.footer in message.text.html:
            return
        # todo: and also compare with db entry

        logging.info("editing MASTER text")
        with contextlib.suppress(MessageNotModified):
            await message.edit_text(format_text(message.text.html))

        for lang_key, slave_post_id in (await get_slave_post_ids(message.id)).items():
            lang = SLAVE_DICT[lang_key]
            translated_text = format_text(translate(message.text.html, lang), lang)

            logging.info("editing SLAVE text")
            with contextlib.suppress(MessageNotModified):
                slave_post = await client.edit_message_text(chat_id=lang.channel_id, message_id=slave_post_id,
                                                            text=translated_text)
            logging.info(slave_post)

    @app.on_deleted_messages(bf)
    async def handle_deleted(client: Client, messages: List[Message]):
        logging.info(f">>>>>> handle_deleted: {messages}", )
        slave_ids = {}
        for message in messages:
            slaves = await get_slave_post_ids(message.id)
            if len(slaves) == 0:
                continue
            for lang_key, slave_post_id in slaves.items():
                if lang_key not in slave_ids:
                    slave_ids[lang_key] = []
                slave_ids[lang_key].append(slave_post_id)

        for lang_key, slave_post_ids in slave_ids.items():
            lang = SLAVE_DICT[lang_key]
            await client.delete_messages(chat_id=lang.channel_id, message_ids=slave_post_ids)

    await app.start()
    logging.info("RUN")
    print("RUNNING...")
    await idle()


if __name__ == "__main__":
    setup_logging()
    setup_event_loop_policy()

    with contextlib.suppress(KeyboardInterrupt):
        run(main())
