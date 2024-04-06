import json
import logging

import deepl
import regex as re
from deep_translator import GoogleTranslator
from deepl import QuotaExceededException, SplitSentences

from config import DEEPL
from data.lang import Language, MASTER, SLAVES

# Load JSON data once
flags_data = {lang.lang_key: json.load(open(rf"./res/{lang.lang_key}/flags.json", "r", encoding="utf-8")) for lang in
              [MASTER] + SLAVES}

# Compile regex pattern
pattern = re.compile(r'#\w+\s|\s{2,}')


def translate(text: str, lang: Language) -> str:
    if lang.lang_key_deepl is not None:
        for index in range(len(DEEPL)):
            try:
                translator = deepl.Translator(DEEPL[index])
                return translator.translate_text(text,
                                                 target_lang=lang.lang_key_deepl,
                                                 split_sentences=SplitSentences.ALL,
                                                 tag_handling="html",
                                                 preserve_formatting=True).text
            except QuotaExceededException:
                logging.info("--- Quota exceeded. Trying other api key ---")
                continue

    logging.error("--- Falling back to Google ---")
    return GoogleTranslator(source="de", target=lang.lang_key).translate(text=text)


def format_text(text: str, lang: Language = MASTER) -> str:
    caption = pattern.sub("", text.replace(lang.footer, "")).strip()
    flag_names = flags_data[lang.lang_key]
    hashtags = " #".join({flag_names[flag] for flag in flag_names if flag in caption})
    formatted = f"{caption}\n\n#{hashtags}\n{lang.footer}"
    logging.info(f">>>>>>>> formatted:\n{formatted}\n")
    return formatted
