"""Simple PELT-style change-point detection for mean shifts."""

from __future__ import annotations

import math

import numpy as np


def _segment_cost(cumulative_sum: np.ndarray, cumulative_square_sum: np.ndarray, start: int, end: int) -> float:
    """Return the sum of squared deviations for a segment [start, end)."""
    length = end - start
    if length <= 0:
        return 0.0

    segment_sum = cumulative_sum[end] - cumulative_sum[start]
    segment_square_sum = cumulative_square_sum[end] - cumulative_square_sum[start]
    mean_square_component = (segment_sum * segment_sum) / length
    return float(segment_square_sum - mean_square_component)


def detect_mean_shift_pelt(values: np.ndarray, penalty_multiplier: float = 2.5) -> list[int]:
    """Detect mean shifts using a lightweight PELT implementation."""
    series = np.asarray(values, dtype=float)
    if len(series) < 4 or np.allclose(series, series[0]):
        return []

    variance = float(np.nanvar(series))
    if not np.isfinite(variance) or variance == 0.0:
        return []

    penalty = penalty_multiplier * variance * math.log(len(series))
    cumulative_sum = np.zeros(len(series) + 1)
    cumulative_square_sum = np.zeros(len(series) + 1)
    cumulative_sum[1:] = np.cumsum(series)
    cumulative_square_sum[1:] = np.cumsum(series * series)

    optimal_cost = np.zeros(len(series) + 1)
    optimal_cost[0] = -penalty
    candidate_sets: list[list[int]] = [[] for _ in range(len(series) + 1)]
    admissible = [0]

    for end in range(1, len(series) + 1):
        candidate_scores = []
        for start in admissible:
            score = optimal_cost[start] + _segment_cost(cumulative_sum, cumulative_square_sum, start, end) + penalty
            candidate_scores.append((score, start))

        best_score, best_start = min(candidate_scores, key=lambda item: item[0])
        optimal_cost[end] = best_score
        candidate_sets[end] = candidate_sets[best_start] + [best_start]

        pruned = []
        for start in admissible:
            score = optimal_cost[start] + _segment_cost(cumulative_sum, cumulative_square_sum, start, end)
            if score <= optimal_cost[end] + penalty:
                pruned.append(start)
        pruned.append(end)
        admissible = pruned

    change_points = [point for point in candidate_sets[len(series)] if point not in {0, len(series)}]
    return sorted(set(change_points))

