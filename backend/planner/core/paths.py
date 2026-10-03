"""Shortest path and containment recommendation stub (Phase 3 contract).

Implements Dijkstra on additive weights w = -ln(p) and evaluates node isolation options.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import ContainmentOption, PathResult

if TYPE_CHECKING:
    from .graph import Network


def most_probable_path(
    network: Network, source_id: str, target_id: str
) -> PathResult | None:
    """Find the most probable attack path from source_id to target_id.

    Contract:
      - Uses Dijkstra under edge weights w = -ln(p) >= 0.
      - Total path probability = exp(-distance).
      - Returns PathResult(nodes=[...], probability=..., total_weight=...)
        or None if no directed network path exists.
    """
    raise NotImplementedError("most_probable_path is scheduled for Phase 3 implementation.")


def attack_paths_to_critical(
    network: Network, source_id: str
) -> list[PathResult]:
    """Discover most probable attack paths from source_id to all critical assets.

    Contract:
      - Critical assets defined as nodes with criticality >= network.meta.critical_threshold.
      - Returns list of PathResult objects sorted by highest probability descending.
    """
    raise NotImplementedError("attack_paths_to_critical is scheduled for Phase 3 implementation.")


def recommend_containment(
    network: Network, compromised_ids: list[str]
) -> list[ContainmentOption]:
    """Recommend candidate containment/isolation points to mitigate ongoing incidents.

    Contract:
      - Evaluates candidate nodes whose removal interrupts attack routes.
      - For each candidate:
          - paths_covered: count of attack paths to critical assets severed.
          - risk_before: aggregate initial risk score.
          - risk_after: aggregate risk score with candidate node isolated (network.without_node).
          - risk_removed_pct: ((risk_before - risk_after) / risk_before) * 100.
          - disruption_cost: candidate node criticality (ADR-003).
      - Returns list of ContainmentOption sorted by highest risk reduction.
    """
    raise NotImplementedError("recommend_containment is scheduled for Phase 3 implementation.")
