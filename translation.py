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
HASHTAG_PATTERN = re.compile(r'(\s{2,})?(#\w+\s)+', re.IGNORECASE)
FLAG_PATTERN = re.compile(u'[\U0001F1E6-\U0001F1FF]{2}|\U0001F3F4|\U0001F3F3', re.UNICODE)


def deepl_translate(text: str, lang: Language) -> str:
    print(DEEPL)
    for api_key in DEEPL:
        print(api_key)
        try:
            return deepl.Translator(api_key).translate_text(text,
                                                            target_lang=lang.lang_key_deepl,
                                                            split_sentences=SplitSentences.ALL,
                                                            tag_handling="html",
                                                            preserve_formatting=True).text
        except QuotaExceededException:
            logging.info("--- Quota exceeded. Trying other api key ---")
            continue

    logging.error("--- All quotas exceeded. Falling back to Google ---")


def translate(text: str, lang: Language) -> str:
    if lang.lang_key_deepl:
        if translation := deepl_translate(text, lang):
            return translation

    return GoogleTranslator(source=MASTER.lang_key, target=lang.lang_key).translate(text=text)


def format_text(text: str, lang: Language = MASTER) -> str:
    caption = HASHTAG_PATTERN.sub("", text.replace(lang.footer, "")).strip()

    flags_in_caption = set(FLAG_PATTERN.findall(caption))
    flag_names = sorted({
        flags_data[lang.lang_key][flag]
        for flag in flags_in_caption
        if flag in flags_data[lang.lang_key]
    })
    hashtags = f"\n#{' #'.join(flag_names)}" if flag_names else ""

    formatted = f"{caption}\n{hashtags}\n{lang.footer}"
    logging.info(f">>>>>>>> formatted:\n{formatted}\n")
    return formatted
