import json
import logging

import deepl
import regex as re
from deep_translator import GoogleTranslator
from deepl import QuotaExceededException, SplitSentences

from config import DEEPL
from data.lang import Language


def translate(text: str, deepl_index: int, lang: Language) -> str:
    try:
        translated_text = deepl.Translator(DEEPL[deepl_index]).translate_text(text,
                                                                              target_lang=lang.lang_key_deepl,
                                                                              split_sentences=SplitSentences.ALL,
                                                                              tag_handling="html",
                                                                              preserve_formatting=True
                                                                              ).text
    except QuotaExceededException:
        if deepl_index < len(DEEPL) - 1:
            logging.info("--- Quota exceeded. Trying other api key ---")
            translated_text = translate(text, deepl_index + 1, lang)
        else:
            logging.error("--- Quota for all api keys exceeded. Now using Google ---")
            translated_text = GoogleTranslator(source="de", target=lang.lang_key).translate(text=text)
    except Exception as e:
        logging.error(f"--- other error translating --- {e}")
        translated_text = GoogleTranslator(source="de", target=lang.lang_key).translate(text=text)

    return translated_text


def format_text(text: str, lang: Language) -> str:
    caption = re.sub(r'#\w+\s|\s{2,}', "", text).strip()

    with open(rf"./res/{lang.lang_key}/flags.json", "r", encoding="utf-8") as file:
        flag_names = json.load(file)
    hashtags = " #".join({flag_names[flag] for flag in flag_names if flag in caption})

    formatted = f"🚨 #{lang.breaking}\n\n{caption}\n\n#{hashtags}\n{lang.footer}"
    logging.info(f">>>>>>>> formatted:\n{formatted}")
    return formatted
