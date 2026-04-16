from __future__ import annotations

from pathlib import Path
import unittest

from pipelines.v2.translation import load_translation_dictionary, translate_value


ROOT = Path(__file__).resolve().parents[2]
DICTIONARY = load_translation_dictionary(str(ROOT / "translation" / "es_en_dictionary.yaml"))


class TranslationTests(unittest.TestCase):
    def test_translate_event_type_exact_match(self) -> None:
        english, strategy, _, normalized = translate_value("SISMO", "event_type", DICTIONARY)

        self.assertEqual(english, "Earthquake")
        self.assertEqual(strategy, "exact_dictionary_match")
        self.assertEqual(normalized, "sismo")

    def test_translate_institution_with_token_dictionary(self) -> None:
        english, strategy, _, _ = translate_value("CMGRD DE CHARTA", "known_or_handled_by", DICTIONARY)

        self.assertEqual(english, "Municipal Disaster Risk Management Council of Charta")
        self.assertEqual(strategy, "token_dictionary_match")

    def test_translate_municipality_as_proper_noun_passthrough(self) -> None:
        english, strategy, _, _ = translate_value("BUCARAMANGA", "municipality", DICTIONARY)

        self.assertEqual(english, "Bucaramanga")
        self.assertEqual(strategy, "proper_noun_passthrough")


if __name__ == "__main__":
    unittest.main()
