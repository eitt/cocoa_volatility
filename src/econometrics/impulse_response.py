"""Impulse-response helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from src.descriptive.visualization import PROJECT_PALETTE, split_legend_columns


def compute_impulse_response(var_result, steps: int = 12):
    """Compute impulse-response functions from a fitted VAR model."""
    return var_result.irf(steps)


def save_impulse_response_plot(
    irf_result,
    output_path: str | Path,
    variable_names: list[str] | None = None,
    acronym_map: dict[str, str] | None = None,
    label_map: dict[str, str] | None = None,
    title: str = "Impulse-response functions",
):
    """Save a customized impulse-response matrix with acronym and legend footer."""
    names = variable_names or getattr(irf_result.model, "endog_names", None)
    if not names:
        names = [f"series_{index + 1}" for index in range(irf_result.irfs.shape[1])]

    horizons = np.arange(irf_result.irfs.shape[0])
    impulse_responses = irf_result.irfs
    standard_errors = irf_result.stderr(orth=False)
    lower_band = impulse_responses - 1.96 * standard_errors
    upper_band = impulse_responses + 1.96 * standard_errors

    panel_count = len(names)
    fig, axes = plt.subplots(
        panel_count,
        panel_count,
        figsize=(4.1 * panel_count, 3.1 * panel_count),
        sharex=True,
    )
    if panel_count == 1:
        axes = np.array([[axes]])

    for response_index, response_name in enumerate(names):
        for impulse_index, impulse_name in enumerate(names):
            axis = axes[response_index, impulse_index]
            line_color = PROJECT_PALETTE[impulse_index % len(PROJECT_PALETTE)]
            axis.fill_between(
                horizons,
                lower_band[:, response_index, impulse_index],
                upper_band[:, response_index, impulse_index],
                color=line_color,
                alpha=0.18,
            )
            axis.plot(
                horizons,
                impulse_responses[:, response_index, impulse_index],
                color=line_color,
                linewidth=2,
            )
            axis.axhline(0, color=PROJECT_PALETTE[7], linestyle="--", linewidth=1)
            axis.grid(True, alpha=0.25, linestyle="--")

            if response_index == 0:
                axis.set_title(
                    f"Shock: {(acronym_map or {}).get(impulse_name, impulse_name)}",
                    fontsize=10,
                    pad=10,
                )
            if impulse_index == 0:
                axis.set_ylabel(
                    "Response\n"
                    f"{(acronym_map or {}).get(response_name, response_name)}",
                    fontsize=10,
                )
            if response_index == panel_count - 1:
                axis.set_xlabel("Months")

    fig.suptitle(title, fontsize=14)

    footer_lines = [
        "solid line = impulse-response estimate",
        "shaded band = approx. 95% interval",
        "dashed line = zero reference",
    ]
    footer_lines.extend(
        [
            f"{(acronym_map or {}).get(name, name)} = {(label_map or {}).get(name, name)}"
            for name in names
        ]
    )
    footer_columns = split_legend_columns(footer_lines, legend_columns=3)
    footer_rows = max(len(column_entries) for column_entries in footer_columns)
    footer_height = min(0.28, 0.06 + 0.035 * footer_rows)
    fig.tight_layout(rect=[0, footer_height, 1, 0.95])

    footer_ax = fig.add_axes([0.03, 0.015, 0.94, max(0.06, footer_height - 0.02)])
    footer_ax.set_axis_off()
    footer_ax.patch.set_visible(True)
    footer_ax.patch.set_facecolor("white")
    footer_ax.patch.set_edgecolor("#cbd5e1")
    footer_ax.patch.set_linewidth(0.8)

    column_width = 1.0 / len(footer_columns)
    for column_index, column_entries in enumerate(footer_columns):
        footer_ax.text(
            column_index * column_width + 0.02 * column_width,
            0.5,
            "\n".join(column_entries),
            ha="left",
            va="center",
            fontsize=8,
            family="monospace",
            transform=footer_ax.transAxes,
        )

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return path
