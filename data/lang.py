from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class Destination:
    channel_id: int
    footer: str
    breaking: str
    announce: str
    advertise: str
    username: str
    chat_id: int = None
    lang_key_deepl: str = None
    # captcha:str


MASTER_KEY = "de",  # German
MASTER = Destination(
    -1001391125365,
    #   -1001240262412,  # https://t.me/MilitaerNews
    "🔰 Abonniere @MilitaerNews\n🔰 Diskutiere im @MNChat",
    "EILMELDUNG",
    "MITTEILUNG",
    "WERBUNG",
    "MilitaerNews",
    -1001526741474,  # https://t.me/MNChat
)

slaves: Dict[str, Destination] = {
    "en":  # English - en-us
    Destination(

        -1001258430463,  # https://t.me/MilitaryNewsEN
        "🔰 Subscribe to @MilitaryNewsEN\n🔰 Join us @MilitaryChatEN",
        "BREAKING",
        "ANNOUNCEMENT",
        "ADVERTISEMENT",
        "MilitaryNewsEN",
        -1001382962633,  # https://t.me/MilitaryChatEN
        lang_key_deepl="en-us"
    ),
    "tr":  # Turkish
    Destination(

        -1001712502236,  # https://t.me/MilitaryNewsTR
        "🔰 @MilitaryNewsTR'e abone olun",
        "SON_DAKİKA",
        "DUYURU",
        "ADVERTISING",
        "MilitaryNewsTR",
    ),
    "fa":  # Persian
    Destination(

        -1001568841775,  # https://t.me/MilitaryNewsFA
        "\nعضو شوید:\n🔰 @MilitaryNewsFA",
        "خبرفوری",
        "اعلامیه",
        "تبلیغات",
        "MilitaryNewsFA",
    ),
    "ru":  # Russian
    Destination(

        -1001330302325,  # https://t.me/MilitaryNewsRU
        "🔰 Подписывайтесь на @MilitaryNewsRU",
        "СРОЧНЫЕ_НОВОСТИ",
        "ОБЪЯВЛЕНИЕ",
        "РЕКЛАМА",
        "MilitaryNewsRU",
    ),
    "pt":  # Portugese - pt-br
    Destination(

        -1001614849485,  # https://t.me/MilitaryNewsBR
        "🔰 Se inscreva no @MilitaryNewsBR",
        "NOTÍCIAS_URGENTES",
        "MENSAGEM",
        "PUBLICIDADE",
        "MilitaryNewsBR",
        lang_key_deepl="pt-br"
    ),
    "es":  # Spanish
    Destination(

        -1001715032604,  # https://t.me/MilitaryNewsES
        "🔰 Suscríbete a @MilitaryNewsES",
        "ÚLTIMA_HORA",
        "ANUNCIO",
        "PUBLICIDAD",
        "MilitaryNewsES",
    ),
    "fr":  # French
    Destination(

        -1001337262241,  # https://t.me/MilitaryNewsFR
        "🔰 Abonnez-vous à @MilitaryNewsFR",
        "BREAKING_NEWS",
        "ANNONCE",
        "PUBLICITÉ",
        "MilitaryNewsFR",
    ),
    "it":  # Italian
    Destination(

        -1001632091535,  # https://t.me/MilitaryNewsITA
        "🔰 iscriviti a @MilitaryNewsITA",
        "ULTIME_NOTIZIE",
        "ANNUNCIO",
        "PUBBLICITÀ",
        "MilitaryNewsITA",
    ),
    "ar":  # Arabic
    Destination(

        -1001972272205,  # https://t.me/MilitaryNewsAR
        "@MilitaryNewsAR اشترك ب أخبار عسكرية بالعربية 🔰\n",
        "معلومات",
        "إشعار",
        "إعلان",
        "MilitaryNewsAR",
    ),
}

type Slave= Tuple[str,Destination]