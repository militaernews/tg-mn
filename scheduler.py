"""
Scheduler for tg-mn: takes posts queued by ptb-suggest's /synthesize
"Veröffentlichen" button (see queued_posts / data/db.py) and hands each one
off to Telegram's own native message scheduling in the MASTER (German)
channel, via the Premium account's real MTProto session - the Bot API (what
ptb-mn otherwise runs on) has no schedule_date equivalent at all, so this is
the only way to actually place a message that Telegram itself holds and
publishes later.

"Next free slot" = SCHEDULE_MIN_GAP_MINUTES after whatever is already
scheduled in the channel (our own earlier hand-offs, or anything a human
scheduled directly there, e.g. a recurring ad), pushed past the configured
quiet window (default 20:00-07:00 local time) if it would otherwise land
there.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from zoneinfo import ZoneInfo

from pyrogram import Client
from pyrogram.errors import RPCError
from pyrogram.types import InputMediaPhoto, InputMediaVideo

import config
from data.db import get_pending_queued_posts, mark_queued_post_scheduled
from data.lang import MASTER

TZ = ZoneInfo(config.SCHEDULE_TIMEZONE)


def _in_quiet_hours(local_dt: datetime) -> bool:
    hour = local_dt.hour
    if config.SCHEDULE_QUIET_START_HOUR > config.SCHEDULE_QUIET_END_HOUR:
        # Window wraps midnight, e.g. 20 -> 7.
        return hour >= config.SCHEDULE_QUIET_START_HOUR or hour < config.SCHEDULE_QUIET_END_HOUR
    return config.SCHEDULE_QUIET_START_HOUR <= hour < config.SCHEDULE_QUIET_END_HOUR


def _push_past_quiet_hours(dt_utc: datetime) -> datetime:
    local = dt_utc.astimezone(TZ)
    if not _in_quiet_hours(local):
        return dt_utc

    quiet_end = local.replace(hour=config.SCHEDULE_QUIET_END_HOUR, minute=0, second=0, microsecond=0)
    if quiet_end <= local:
        quiet_end += timedelta(days=1)
    return quiet_end.astimezone(timezone.utc)


async def _latest_reserved_time(client: Client, chat_id: int) -> Optional[datetime]:
    """Latest time already spoken for in the channel - whatever Telegram
    currently has scheduled there, whether it's our own earlier hand-off or
    something a human scheduled directly (e.g. a recurring ad slot)."""
    try:
        scheduled = await client.get_scheduled_messages(chat_id)
    except RPCError as e:
        logging.warning(f"[scheduler] Could not fetch scheduled messages for {chat_id}: {e}")
        return None

    dates = [m.date for m in scheduled if m.date]
    if not dates:
        return None

    latest = max(dates)
    return latest if latest.tzinfo else latest.replace(tzinfo=timezone.utc)


async def next_free_slot(client: Client, chat_id: int) -> datetime:
    now = datetime.now(timezone.utc)
    latest = await _latest_reserved_time(client, chat_id)

    candidate = now
    if latest is not None:
        candidate = max(candidate, latest + timedelta(minutes=config.SCHEDULE_MIN_GAP_MINUTES))

    return _push_past_quiet_hours(candidate)


async def process_queue(client: Client) -> None:
    """Hand every still-pending queued post off to Telegram's native
    scheduler, one at a time so each new one sees the slot the previous one
    just took.
    """
    pending = get_pending_queued_posts()
    if not pending:
        return

    for row in pending:
        media: List[dict] = json.loads(row["media"]) if row.get("media") else []
        try:
            slot = await next_free_slot(client, MASTER.channel_id)

            if media:
                items = []
                for i, m in enumerate(media):
                    cls = InputMediaPhoto if m["type"] == "photo" else InputMediaVideo
                    kwargs = {"media": m["file_id"]}
                    if i == 0:
                        kwargs["caption"] = row["html"]
                    items.append(cls(**kwargs))
                sent = await client.send_media_group(MASTER.channel_id, items, schedule_date=slot)
                scheduled_message_id = sent[0].id
            else:
                sent = await client.send_message(MASTER.channel_id, row["html"], schedule_date=slot)
                scheduled_message_id = sent.id

            mark_queued_post_scheduled(row["id"], scheduled_message_id, slot)
            logging.info(f"[scheduler] Queued post {row['id']} scheduled for {slot.isoformat()}")

        except Exception as e:
            logging.error(f"[scheduler] Failed to schedule queued post {row['id']}: {e}")
