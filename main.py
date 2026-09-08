"""
tg-mn: MTProto (Pyrogram) session for the MASTER channel.

This used to be the original translate/crosspost/breaking-news pipeline for
the German main channel (MASTER.channel_id) - that job now belongs to
ptb-mn, which does the same thing over the Bot API. Re-registering this
repo's old handlers here too would double-post every single message (once
via ptb-mn, once via this account), so they're intentionally not wired up
any more (translation.py/utils.py/clean_group.py are unused but left in
place for reference/possible future reuse).

What's left, and the only reason this repo is still deployed: a real user
account (not a bot) is the only thing that can use Telegram's native message
scheduling. scheduler.py polls queued_posts (written by ptb-suggest's
/synthesize "Veröffentlichen" button) and hands each one off to Telegram's
own scheduler in the MASTER channel via this account.
"""

import asyncio
import logging
import os
from datetime import datetime

from pyrogram import Client, idle
from pyrogram.enums import ParseMode

import config
from scheduler import process_queue

app = Client(
    name="Premium",
    api_id=config.API,
    api_hash=config.HASH,
    phone_number=config.NUMBER,
    parse_mode=ParseMode.HTML
)


def setup_logging():
    log_filename = f"./logs/{datetime.now().strftime('%Y-%m-%d/%H-%M-%S')}.log"
    os.makedirs(os.path.dirname(log_filename), exist_ok=True)
    logging.basicConfig(
        format="%(asctime)s %(levelname)-5s %(funcName)-20s [%(filename)s:%(lineno)d]: %(message)s",
        encoding="utf-8",
        filename=log_filename,
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logging.getLogger().addHandler(logging.StreamHandler())


async def scheduler_loop():
    while True:
        try:
            await process_queue(app)
        except Exception as e:
            logging.error(f"[scheduler] process_queue failed: {e}")
        await asyncio.sleep(config.SCHEDULE_POLL_INTERVAL_SECONDS)


async def _run():
    await app.start()
    logging.info("Premium account started (scheduler-only mode)")
    asyncio.create_task(scheduler_loop())
    await idle()
    await app.stop()


def main():
    logging.info("-- STARTED // TG-MN (scheduler-only) --")
    print("RUNNING...")
    app.run(_run())


if __name__ == "__main__":
    setup_logging()
    main()
