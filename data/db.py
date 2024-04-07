import inspect
import logging
import sys
from traceback import format_exc
from typing import Dict

import psycopg2
from psycopg2 import OperationalError
from psycopg2.extras import NamedTupleCursor

from config import DATABASE_URL
from data.lang import MASTER
from data.model import Post

conn = psycopg2.connect(DATABASE_URL, cursor_factory=NamedTupleCursor)


def print_psycopg2_exception(err):
    err_type, err_obj, traceback = sys.exc_info()

    # get the line number when exception occured
    #   line_num = traceback.tb_lineno

    #  print ("\npsycopg2 ERROR:", err, "on line number:", line_num)
    #    print ("psycopg2 traceback:", traceback, "-- type:", err_type)

    # psycopg2 extensions.Diagnostics object attribute
    logging.error(f"extensions.Diagnostics: {err.diag}", )
    logging.error(f"pgerror: {err.pgerror} -- pgcode: {err.pgcode}")


def set_post(post: Post):
    try:
        with conn.cursor() as c:
            c.execute("""INSERT INTO posts(
            post_id,lang,msg_id,media_group_id,reply_id,file_type,file_id,text
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);""",
                      (post.post_id, post.lang, post.msg_id, post.media_group_id, post.reply_id, post.file_type,
                       post.file_id, post.text))
        conn.commit()

    except Exception or OperationalError as err:
        print_psycopg2_exception(err)
        conn.rollback()
    except Exception as e:
        logging.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed {repr(e)} - {format_exc()}")


def update_post_media(lang: str, msg_id: int, file_type: int, file_id: str):
    try:
        with conn.cursor() as c:
            c.execute("""UPDATE posts SET file_type=%s,file_id=%s WHERE lang=%s and msg_id=%s;""",
                      (file_type, file_id, lang, msg_id,))
        conn.commit()

    except Exception or OperationalError as err:
        print_psycopg2_exception(err)
        conn.rollback()
    except Exception as e:
        logging.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed {repr(e)} - {format_exc()}")


def get_slave_post_ids(master_post_id: int) -> Dict[str, int]:
    try:
        with conn.cursor() as c:

            c.execute(
                "select lang,msg_id from posts where post_id = %s and lang != %s;",
                (master_post_id, MASTER.lang_key),
            )
            result = c.fetchmany()
            logging.info(f">>>>>>>>>>>>>>>>>>>>>>>> get_posts >>>>>>>>>>>>>>>>> POSTS: {result}")

# this may not return a post for all supported languages, if something went wrong when inserting
            return {post[0]: post[1] for post in result}
    except OperationalError as err:
        print_psycopg2_exception(err)
        conn.rollback()
    except Exception as e:
        logging.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed {repr(e)} - {format_exc()}")


def get_file_id(lang_key: str, msg_id: int, ) -> int:
    try:
        with conn.cursor() as c:

            c.execute("select file_id from posts where lang = %s and msg_id = %s;",
                      (lang_key, msg_id))
            s: int = c.fetchone()[0]

            logging.info(f">>>>>>>>>>>>>>>>>>>>>>>> get_post >>>>>>>>>>>>>>>>> POST: {s}", )

            return s

    except OperationalError as err:
        print_psycopg2_exception(err)
        conn.rollback()
    except Exception as e:
        logging.error(f"{inspect.currentframe().f_code.co_name} — DB-Operation failed {repr(e)} - {format_exc()}")
