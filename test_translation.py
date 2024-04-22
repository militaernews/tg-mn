from unittest.mock import patch, MagicMock

import pytest
from deepl import QuotaExceededException, Translator

import data.lang
from translation import deepl_translate, translate, format_text

DE = data.lang.MASTER
EN = data.lang.SLAVES[0]
FR = data.lang.SLAVES[1]


@pytest.fixture
def mock_translator():
    with patch('translation.deepl.Translator.translate_text') as mock_deepl, \
            patch('translation.GoogleTranslator.translate') as mock_google, :
        yield mock_deepl, mock_google




@pytest.mark.parametrize("text, lang, expected_translation", [
    ("Hallo", DE, "Hallo",),
    ("Hallo", EN, "Hello",),
    ("Hallo", FR, "Bonjour",),
], ids=["master", "deepl", "google"])
def test_translate(mock_translator, text, lang, expected_translation):
    mock_translator[0].return_value.text = expected_translation
    mock_translator[1].return_value = expected_translation

    translation = translate(text, lang)

    assert translation == expected_translation


@pytest.mark.parametrize("text, lang, expected_output", [
    ("Hello #world", DE, "Hello\n\nFooter"),
    ("Hello", EN, "Hello\n\n#USA\nFooter"),
], ids=["without-flag", "with-flag"])
def test_format_text(text, lang, expected_output, mock_translator):
    with patch('translation.flags_data', {"en": {"🇺🇸": "USA"}}):
        formatted_text = format_text(text, lang)

        assert formatted_text == expected_output
