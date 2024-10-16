import logging
from functools import wraps
from typing import Dict


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
