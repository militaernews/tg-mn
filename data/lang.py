from dataclasses import dataclass
from typing import Dict


@dataclass
class Language:
    lang_key: str
    channel_id: int
    footer: str
    breaking: str
    announce: str
    advertise: str
    username: str
    chat_id: int = None
    lang_key_deepl: str = None
    # captcha:str


MASTER = Language(
    "de",  # German
    -1001391125365,
    ##   -1001240262412,  # https://t.me/MilitaerNews
    "🔰 Abonniere @MilitaerNews\n🔰 Diskutiere im @MNChat",
    "EILMELDUNG",
    "MITTEILUNG",
    "WERBUNG",
    "MilitaerNews",
    -1001526741474,  # https://t.me/MNChat
)

SLAVES: [Language] = [

    Language(
        "en",  # English - en-us
        -1001391125365,
      ##  -1001258430463,  # https://t.me/MilitaryNewsEN
        "🔰 Subscribe to @MilitaryNewsEN\n🔰 Join us @MilitaryChatEN",
        "BREAKING",
        "ANNOUNCEMENT",
        "ADVERTISEMENT",
        "MilitaryNewsEN",
        -1001382962633,  # https://t.me/MilitaryChatEN
        lang_key_deepl="en-us"
    ),


]

SLAVE_DICT = {slave.lang_key: slave for slave in SLAVES}
