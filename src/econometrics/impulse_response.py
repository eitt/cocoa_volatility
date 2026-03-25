"""Impulse-response helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


def compute_impulse_response(var_result, steps: int = 12):
    """Compute impulse-response functions from a fitted VAR model."""
    return var_result.irf(steps)


def save_impulse_response_plot(irf_result, output_path: str | Path):
    """Save the default orthogonalized impulse-response plot."""
    fig = irf_result.plot(orth=False)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path

