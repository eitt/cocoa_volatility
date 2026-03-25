"""File and configuration helpers for the cocoa volatility project."""

from __future__ import annotations

import ast
from datetime import date
from pathlib import Path
import re
from typing import Any

import pandas as pd

try:
    import yaml
except ImportError:  # pragma: no cover - environment dependent
    yaml = None


def _parse_scalar(value: str) -> Any:
    """Parse a simple YAML scalar into a Python value."""
    normalized = value.strip()
    if normalized in {"null", "Null", "~"}:
        return None
    if normalized in {"true", "True"}:
        return True
    if normalized in {"false", "False"}:
        return False

    try:
        if normalized.startswith(("'", '"', "[", "{", "(")):
            return ast.literal_eval(normalized)
        if re.fullmatch(r"-?\d+", normalized):
            return int(normalized)
        if re.fullmatch(r"-?\d+\.\d*", normalized):
            return float(normalized)
    except (SyntaxError, ValueError):
        return normalized

    return normalized


def _parse_simple_yaml_lines(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    """Parse a simple indentation-based YAML subset."""
    if index >= len(lines):
        return {}, index

    _, content = lines[index]
    if content.startswith("- "):
        return _parse_simple_yaml_sequence(lines, index, indent)
    return _parse_simple_yaml_mapping(lines, index, indent)


def _parse_simple_yaml_mapping(
    lines: list[tuple[int, str]],
    index: int,
    indent: int,
) -> tuple[dict[str, Any], int]:
    """Parse a mapping block."""
    mapping: dict[str, Any] = {}

    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent < indent or (current_indent == indent and content.startswith("- ")):
            break
        if current_indent > indent:
            nested_value, index = _parse_simple_yaml_lines(lines, index, current_indent)
            if isinstance(nested_value, dict):
                mapping.update(nested_value)
            continue

        key, _, remainder = content.partition(":")
        value_text = remainder.strip()

        if value_text:
            mapping[key.strip()] = _parse_scalar(value_text)
            index += 1
            continue

        if index + 1 < len(lines) and lines[index + 1][0] > current_indent:
            nested_value, index = _parse_simple_yaml_lines(lines, index + 1, lines[index + 1][0])
            mapping[key.strip()] = nested_value
        else:
            mapping[key.strip()] = None
            index += 1

    return mapping, index


def _parse_simple_yaml_sequence(
    lines: list[tuple[int, str]],
    index: int,
    indent: int,
) -> tuple[list[Any], int]:
    """Parse a sequence block."""
    sequence: list[Any] = []

    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent != indent or not content.startswith("- "):
            break

        item_text = content[2:].strip()
        mapping_match = re.match(r"^([A-Za-z0-9_]+):(.*)$", item_text)

        if not item_text:
            if index + 1 < len(lines) and lines[index + 1][0] > current_indent:
                nested_value, index = _parse_simple_yaml_lines(lines, index + 1, lines[index + 1][0])
                sequence.append(nested_value)
            else:
                sequence.append(None)
                index += 1
            continue

        if mapping_match:
            key = mapping_match.group(1).strip()
            remainder = mapping_match.group(2).strip()
            item: dict[str, Any] = {key: _parse_scalar(remainder)} if remainder else {key: None}
            index += 1

            if index < len(lines) and lines[index][0] > current_indent:
                nested_value, index = _parse_simple_yaml_mapping(lines, index, lines[index][0])
                item.update(nested_value)

            sequence.append(item)
            continue

        sequence.append(_parse_scalar(item_text))
        index += 1

    return sequence, index


def _load_simple_yaml(path: str | Path) -> dict[str, Any]:
    """Load a minimal subset of YAML used by this project without PyYAML."""
    raw_lines = Path(path).read_text(encoding="utf-8").splitlines()
    lines = []
    for raw_line in raw_lines:
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        lines.append((indent, raw_line.strip()))

    parsed, _ = _parse_simple_yaml_lines(lines, 0, lines[0][0] if lines else 0)
    return parsed or {}


def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load a YAML file into a dictionary."""
    if yaml is not None:
        with Path(path).open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    return _load_simple_yaml(path)


def ensure_directory(path: str | Path) -> Path:
    """Create a directory if it does not already exist."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def build_timestamped_filename(stem: str, suffix: str, run_date: date | None = None) -> str:
    """Return an ISO-dated output filename."""
    active_date = run_date or date.today()
    return f"{active_date.isoformat()}_{stem}{suffix}"


def write_dataframe(dataframe: pd.DataFrame, output_path: str | Path, index: bool = False) -> Path:
    """Write a dataframe using an output format inferred from the suffix."""
    path = Path(output_path)
    ensure_directory(path.parent)

    if path.suffix == ".csv":
        dataframe.to_csv(path, index=index)
    elif path.suffix == ".xlsx":
        dataframe.to_excel(path, index=index)
    elif path.suffix == ".parquet":
        dataframe.to_parquet(path, index=index)
    else:
        raise ValueError(f"Unsupported output format: {path.suffix}")

    return path
