import logging
from functools import wraps
from typing import Dict, List
from datetime import datetime

from psycopg_pool import ConnectionPool

from config import DATABASE_URL
from data.lang import MASTER
from data.model import Post


def db_operation(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            with ConnectionPool(DATABASE_URL, open=False) as pool:
                with pool.connection() as connection:
                     with connection.cursor() as cursor:
                        result = func(cursor, *args, **kwargs)
                connection.commit()
            logging.info(f"{func.__name__} RESULT: {result}")
            return result
        except  Exception as e:
            logging.error(f"{func.__name__} failed: {e}")
            connection.rollback()

    return wrapper


@db_operation
def set_post(c, post: Post):
    c.execute("""INSERT INTO posts(
            post_id,lang,msg_id,media_group_id,reply_id,file_type,file_id,text,spoiler
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s);""",
              (post.post_id, post.lang, post.msg_id, post.media_group_id, post.reply_id,
               post.file_type,
               post.file_id, post.text, post.spoiler))


@db_operation
def update_post_media(c, lang: str, msg_id: int, file_type: int, file_id: str):
    # todo support spoiler
    c.execute("""UPDATE posts SET file_type=%s,file_id=%s WHERE lang=%s and msg_id=%s;""",
              (file_type, file_id, lang, msg_id,))


@db_operation
def get_slave_post_ids(c, master_post_id: int) -> Dict[str, int]:
    c.execute(
        "select lang,msg_id from posts where post_id = %s and lang != %s;",
        (master_post_id, MASTER.lang_key),
    )
    result = c.fetchmany()

    # this may not return a post for all supported languages, if something went wrong when inserting
    return {post[0]: post[1] for post in result}


@db_operation
def get_file_id(c, lang_key: str, msg_id: int, ) -> int:
    c.execute("select file_id from posts where lang = %s and msg_id = %s;",
              (lang_key, msg_id))
    s: int = (c.fetchone())[0]
    return s


@db_operation
def get_pending_queued_posts(c) -> List[dict]:
    """Posts handed off by ptb-suggest's /synthesize "Veröffentlichen" button,
    not yet scheduled into the MASTER channel - oldest first (see
    scheduler.py). Shares the same DB as ptb-suggest/ptb-mn.
    """
    c.execute(
        "select id, html, media from queued_posts "
        "where handed_off_at is null order by created_at asc"
    )
    rows = c.fetchall()
    return [{"id": row[0], "html": row[1], "media": row[2]} for row in rows]


@db_operation
def mark_queued_post_scheduled(c, post_id: int, scheduled_message_id: int, scheduled_at: datetime) -> None:
    """Record that a queued post was handed off to Telegram's own scheduler."""
    c.execute(
        "update queued_posts set handed_off_at=now(), scheduled_message_id=%s, scheduled_at=%s "
        "where id=%s",
        (scheduled_message_id, scheduled_at, post_id))
