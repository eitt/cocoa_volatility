"""Copy manuscript assets into a self-contained LaTeX bundle under paper/."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.outputs.latex_bundle import (  # noqa: E402
    build_latex_bundle_manifest,
    copy_file,
    copy_tree_files,
)
from src.utils.file_utils import load_yaml, write_dataframe  # noqa: E402
from src.utils.logging_utils import get_project_logger  # noqa: E402

PATHS = load_yaml(ROOT / "config" / "paths.yaml")


def main() -> None:
    """Prepare a portable LaTeX bundle in the paper folder."""
    logger = get_project_logger("12_prepare_latex_bundle", ROOT / PATHS["output_logs"])

    paper_dir = ROOT / "paper"
    figures_dir = paper_dir / "figures"
    tables_dir = paper_dir / "tables"
    references_dir = paper_dir / "references"

    records: list[dict[str, object]] = []
    records.extend(copy_tree_files(ROOT / PATHS["output_figures"], figures_dir))
    records.extend(copy_tree_files(ROOT / PATHS["output_tables"], tables_dir))
    records.append(
        copy_file(
            ROOT / "references" / "cocoa_volatility.bib",
            references_dir / "cocoa_volatility.bib",
        )
    )
    records.append(
        copy_file(
            ROOT / "docs" / "citation_justification.md",
            references_dir / "citation_justification.md",
        )
    )

    manifest = build_latex_bundle_manifest(records)
    write_dataframe(manifest, paper_dir / "latex_bundle_manifest.csv")
    logger.info(
        "Prepared LaTeX bundle with %s copied assets under %s",
        len(manifest),
        paper_dir,
    )


if __name__ == "__main__":
    main()
