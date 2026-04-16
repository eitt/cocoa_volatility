"""Deterministic Spanish-to-English translation helpers for v2."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import re
import unicodedata

import pandas as pd

from src.utils.file_utils import load_yaml


GENERIC_CONTEXT = "generic"


@dataclass(frozen=True)
class TranslationEntry:
    """One reusable translation rule."""

    original_spanish_term: str
    normalized_spanish_term: str
    english_translation: str
    context: str
    notes: str


def normalize_spanish_text(value: object) -> str:
    """Normalize Spanish text for matching."""
    if value is None or (isinstance(value, float) and pd.isna(value)) or value is pd.NA:
        return ""

    text = str(value).replace("\ufeff", "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(character for character in text if not unicodedata.combining(character))
    text = re.sub(r"[^a-z0-9/\-\s]", " ", text)
    text = text.replace("/", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _load_entries(path: str) -> list[TranslationEntry]:
    """Load dictionary entries from YAML."""
    raw_dictionary = load_yaml(path)
    entries: list[TranslationEntry] = []
    for original_term, metadata in raw_dictionary.items():
        if not isinstance(metadata, dict):
            continue
        normalized = metadata.get("normalized_spanish_term") or normalize_spanish_text(original_term)
        entries.append(
            TranslationEntry(
                original_spanish_term=original_term,
                normalized_spanish_term=normalized,
                english_translation=metadata.get("english_translation", str(original_term)),
                context=metadata.get("context", GENERIC_CONTEXT),
                notes=metadata.get("notes", ""),
            )
        )
    return entries


def load_translation_dictionary(path: str) -> dict[str, object]:
    """Build exact and token-aware indexes from the translation dictionary."""
    entries = _load_entries(path)
    exact_index: dict[str, list[TranslationEntry]] = defaultdict(list)
    phrase_entries: list[TranslationEntry] = []

    for entry in entries:
        exact_index[entry.normalized_spanish_term].append(entry)
        phrase_entries.append(entry)

    phrase_entries.sort(key=lambda item: len(item.normalized_spanish_term.split()), reverse=True)
    return {
        "entries": entries,
        "exact_index": exact_index,
        "phrase_entries": phrase_entries,
    }


def _pick_entry(entries: list[TranslationEntry], context: str) -> TranslationEntry | None:
    """Pick the best entry for a context, preferring context-specific rules."""
    context_matches = [entry for entry in entries if entry.context == context]
    if context_matches:
        return context_matches[0]
    generic_matches = [entry for entry in entries if entry.context == GENERIC_CONTEXT]
    if generic_matches:
        return generic_matches[0]
    return entries[0] if entries else None


def _title_preserving_small_words(text: str) -> str:
    """Title-case text while keeping common English connectors lowercase."""
    if not text:
        return text

    lower_words = {"of", "the", "and", "or", "in", "on", "at", "for"}
    tokens = text.split()
    formatted = []
    for index, token in enumerate(tokens):
        normalized = token.lower()
        if index > 0 and normalized in lower_words:
            formatted.append(normalized)
        else:
            formatted.append(token[:1].upper() + token[1:])
    return " ".join(formatted)


def _translate_with_tokens(
    normalized_value: str,
    context: str,
    dictionary: dict[str, object],
) -> tuple[str | None, list[str]]:
    """Translate a phrase by greedily applying dictionary entries to token spans."""
    if not normalized_value:
        return None, []

    tokens = normalized_value.split()
    if not tokens:
        return None, []

    matched_terms: list[str] = []
    translated_tokens: list[str] = []
    phrase_entries: list[TranslationEntry] = dictionary["phrase_entries"]

    position = 0
    while position < len(tokens):
        matched_entry: TranslationEntry | None = None
        matched_length = 0
        for entry in phrase_entries:
            if entry.context not in {context, GENERIC_CONTEXT}:
                continue
            candidate_tokens = entry.normalized_spanish_term.split()
            candidate_length = len(candidate_tokens)
            if candidate_length == 0 or candidate_length > len(tokens) - position:
                continue
            if tokens[position : position + candidate_length] == candidate_tokens:
                matched_entry = entry
                matched_length = candidate_length
                break

        if matched_entry is not None:
            translated_tokens.append(matched_entry.english_translation)
            matched_terms.append(matched_entry.normalized_spanish_term)
            position += matched_length
            continue

        translated_tokens.append(tokens[position].title())
        position += 1

    if not matched_terms:
        return None, []

    translated = " ".join(translated_tokens)
    translated = re.sub(r"\s+", " ", translated).strip()
    return _title_preserving_small_words(translated), matched_terms


def translate_value(
    value: object,
    context: str,
    dictionary: dict[str, object],
) -> tuple[str, str, list[str], str]:
    """Translate one categorical value and record the translation strategy."""
    normalized_value = normalize_spanish_text(value)
    exact_index: dict[str, list[TranslationEntry]] = dictionary["exact_index"]

    if not normalized_value:
        return "Not reported", "missing_value", [], normalized_value

    direct_match = _pick_entry(exact_index.get(normalized_value, []), context)
    if direct_match is not None:
        return direct_match.english_translation, "exact_dictionary_match", [direct_match.normalized_spanish_term], normalized_value

    if context in {"municipality"}:
        return _title_preserving_small_words(str(value).strip().title()), "proper_noun_passthrough", [], normalized_value

    token_translation, matched_terms = _translate_with_tokens(normalized_value, context, dictionary)
    if token_translation is not None:
        return token_translation, "token_dictionary_match", matched_terms, normalized_value

    if context in {"locality"}:
        return _title_preserving_small_words(str(value).strip().title()), "locality_passthrough", [], normalized_value

    return _title_preserving_small_words(str(value).strip().title()), "standardized_passthrough", [], normalized_value


def translate_categorical_fields(
    dataframe: pd.DataFrame,
    categorical_columns: list[str],
    dictionary: dict[str, object],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Translate all configured categorical fields and return an audit table."""
    translated = dataframe.copy()
    audit_records: list[dict[str, object]] = []

    for base_name in categorical_columns:
        spanish_column = f"{base_name}_es"
        english_column = f"{base_name}_en"
        if spanish_column not in translated.columns:
            continue

        cache: dict[object, tuple[str, str, list[str], str]] = {}
        unique_values = translated[spanish_column].drop_duplicates().tolist()
        for raw_value in unique_values:
            cache[raw_value] = translate_value(raw_value, base_name, dictionary)

        translated[english_column] = translated[spanish_column].map(lambda value: cache[value][0] if value in cache else "Not reported")

        for raw_value, translation_result in cache.items():
            english_value, strategy, matched_terms, normalized_value = translation_result
            audit_records.append(
                {
                    "context": base_name,
                    "original_value": raw_value if raw_value is not pd.NA else None,
                    "normalized_value": normalized_value,
                    "english_value": english_value,
                    "translation_strategy": strategy,
                    "matched_terms": ", ".join(matched_terms),
                }
            )

    audit_df = pd.DataFrame(audit_records).sort_values(["context", "original_value"], na_position="last").reset_index(drop=True)
    return translated, audit_df
