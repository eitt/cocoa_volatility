"""Configuration helpers for the v2 disaster pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.utils.file_utils import ensure_directory, load_yaml


def load_v2_config(root: Path, config_path: Path | None = None) -> dict[str, Any]:
    """Load the main v2 configuration and its schema companion."""
    resolved_config = config_path or root / "configs" / "v2" / "pipeline_config.yaml"
    config = load_yaml(resolved_config)
    schema_path = root / config["paths"]["schema"]
    config["schema_definition"] = load_yaml(schema_path)
    return config


def resolve_paths(root: Path, config: dict[str, Any]) -> dict[str, Path]:
    """Resolve configured relative paths into absolute paths."""
    return {key: root / relative_path for key, relative_path in config["paths"].items()}


def ensure_output_directories(paths: dict[str, Path]) -> None:
    """Create the output directories required by the pipeline."""
    for key, path in paths.items():
        if key.endswith("_dir") or key.endswith("_root"):
            ensure_directory(path)


def find_input_file(root: Path, config: dict[str, Any]) -> Path:
    """Locate the source CSV using the configured glob pattern."""
    pattern = config["project"]["input_pattern"]
    matches = sorted(root.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No source file found for pattern: {pattern}")
    return matches[0]

