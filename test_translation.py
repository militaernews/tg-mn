import data.lang

from unittest.mock import patch
from translation import translate
from data.lang import Language

DE = data.lang.MASTER
EN = data.lang.SLAVES[0]
FR = data.lang.SLAVES[1]


def test_translate_happy_path_deepl():
    # Arrange

    with patch("translation.deepl_translate", return_value="Hallo, Welt!"):
        # Act
        result = translate("Hello, world!", EN)
        # Assert
        assert result == "Hallo, Welt!"


def test_translate_happy_path_google():
    # Arrange

    with patch("translation.deepl_translate", return_value=None), \
            patch("translation.GoogleTranslator.translate", return_value="Hola, mundo!"):
        # Act
        result = translate("Hello, world!", EN)
        # Assert
        assert result == "Hola, mundo!"


def test_translate_edge_case_empty_string():
    # Arrange

    with patch("translation.deepl_translate", return_value=""):
        # Act
        result = translate("", EN)
        # Assert
        assert result == ""


def test_translate_edge_case_space():
    # Arrange

    with patch("translation.deepl_translate", return_value=None), \
            patch("translation.GoogleTranslator.translate", return_value=" "):
        # Act
        result = translate(" ", EN)
        # Assert
        assert result == " "


def test_translate_error_deepl_exception():
    # Arrange

    with patch("translation.deepl_translate", side_effect=Exception("Deepl translation failed")):
        # Act
        result = translate("Hello, world!", DE)
        # Assert
        assert result == ""
