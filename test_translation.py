from unittest.mock import patch

import pytest
from deepl import QuotaExceededException
from data.lang import Language
import data.lang
from translation import translate, format_text

DE = data.lang.MASTER
EN = Language(
    "en",  # English - en-us
    1,
    "Footer",
    "BREAKING",
    "ANNOUNCEMENT",
    "ADVERTISEMENT",
    "MilitaryNewsEN",
    -1001382962633,  # https://t.me/MilitaryChatEN
    lang_key_deepl="en-us"
)
TR = data.lang.SLAVES[1]


@pytest.fixture(autouse=True)
def set_up():
    with patch("translation.DEEPL", ["key1", "key2"]), patch('translation.flags_data', {
        EN.lang_key: {"🇱🇮": "Liechtenstein", "🏴": "IslamicState"}}):
        yield


def test_translate_deepl_translation():
    with patch('translation.deepl_translate', return_value="Hallo, Welt!"):
        result = translate("Hello, world!", EN)
        assert result == "Hallo, Welt!"


def test_translate_no_lang_key():
    with patch('translation.deepl_translate', return_value=None), \
            patch('translation.GoogleTranslator.translate', return_value="Hola, mundo!"):
        result = translate("Hello, world!", TR)
        assert result == "Hola, mundo!"


def test_translate_quota_exceeded():
    with patch('deepl.Translator.translate_text', side_effect=QuotaExceededException("Quota exceeded")) as deepl_mock, \
            patch('translation.GoogleTranslator.translate', return_value="Fallback translation"):
        result = translate("Hello, world!", EN)
        assert deepl_mock.call_count == 2
        assert result == "Fallback translation"


def test_format_text_happy_path():
    expected_output = "🇱🇮🏴 Hello world\n\n#IslamicState #Liechtenstein\nFooter"

    result = format_text("🇱🇮🏴 Hello world", EN)

    assert result == expected_output


def test_format_text_no_flags():
    expected_output = "Hello world\n\nFooter"

    result = format_text("Hello world", EN)

    assert result == expected_output
