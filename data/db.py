import inspect
import logging
from contextlib import asynccontextmanager
from traceback import format_exc
from typing import Dict, AsyncGenerator

from aiopg import create_pool
from psycopg2 import OperationalError
from psycopg2.extras import NamedTupleCursor

from config import DATABASE_URL
from data.lang import MASTER
from data.model import Post


@asynccontextmanager
async def db_cursor() -> AsyncGenerator:
    try:
        async with create_pool(DATABASE_URL) as pool:
            async with pool.acquire() as conn:
                async with conn.cursor(cursor_factory=NamedTupleCursor) as cursor:
                    yield cursor
    except OperationalError as err:
        logging.error(
            f"{inspect.currentframe().f_code.co_name} — DB-Operation failed!\npgerror: {err.pgerror} -- pgcode: {err.pgcode}\nextensions.Diagnostics: {err.diag}", )
    except Exception as e:
        logging.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed {repr(e)} - {format_exc()}")


async def set_post(post: Post):
    async with db_cursor() as c:
        await c.execute("""INSERT INTO posts(
            post_id,lang,msg_id,media_group_id,reply_id,file_type,file_id,text
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);""",
                        (post.post_id, post.lang, post.msg_id, post.media_group_id, post.reply_id,
                         post.file_type,
                         post.file_id, post.text))


async def update_post_media(lang: str, msg_id: int, file_type: int, file_id: str):
    async with db_cursor() as c:
        await c.execute("""UPDATE posts SET file_type=%s,file_id=%s WHERE lang=%s and msg_id=%s;""",
                        (file_type, file_id, lang, msg_id,))


async def get_slave_post_ids(master_post_id: int) -> Dict[str, int]:
    async with db_cursor() as c:
        await c.execute(
            "select lang,msg_id from posts where post_id = %s and lang != %s;",
            (master_post_id, MASTER.lang_key),
        )
        result = c.fetchmany()
        logging.info(f">>>>>>>>>>>>>>>>>>>>>>>> get_posts >>>>>>>>>>>>>>>>> POSTS: {result}")

        # this may not return a post for all supported languages, if something went wrong when inserting
    return {post[0]: post[1] for post in result}


async def get_file_id(lang_key: str, msg_id: int, ) -> int:
    async with db_cursor() as c:
        await c.execute("select file_id from posts where lang = %s and msg_id = %s;",
                        (lang_key, msg_id))
        s: int = c.fetchone()[0]

    logging.info(f">>>>>>>>>>>>>>>>>>>>>>>> get_post >>>>>>>>>>>>>>>>> POST: {s}", )

    return s
