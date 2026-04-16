"""CLI entrypoint for the v2 disaster pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipelines.v2.pipeline import run_v2_pipeline


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(description="Run the isolated v2 disaster analytics pipeline.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to the current project root.",
    )
    parser.add_argument(
        "--skip-render",
        action="store_true",
        help="Generate markdown and analytical artifacts without calling Pandoc.",
    )
    return parser


def main() -> None:
    """Execute the CLI."""
    parser = build_parser()
    args = parser.parse_args()
    run_v2_pipeline(root=args.root.resolve(), render_outputs=not args.skip_render)


if __name__ == "__main__":
    main()

