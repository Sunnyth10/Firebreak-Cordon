"""Shortest path and containment recommendation engine (Phase 3).

Implements Dijkstra on additive weights w = -ln(p) and evaluates node isolation options.
"""

from __future__ import annotations

import heapq
import math
from typing import TYPE_CHECKING

from .blast import blast_radius
from .models import ContainmentOption, PathResult
from .scoring import compute_score

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
    if source_id not in network.nodes or target_id not in network.nodes:
        return None

    if source_id == target_id:
        return PathResult(nodes=[source_id], probability=1.0, total_weight=0.0)

    # Dijkstra on w = -ln(p)
    dist: dict[str, float] = {source_id: 0.0}
    prev: dict[str, str] = {}
    pq: list[tuple[float, str]] = [(0.0, source_id)]

    while pq:
        d, curr = heapq.heappop(pq)
        if curr == target_id:
            break

        if d > dist.get(curr, float("inf")):
            continue

        for neighbor, prob in network.network_adj.get(curr, []):
            w = -math.log(prob)
            new_dist = d + w
            if new_dist < dist.get(neighbor, float("inf")):
                dist[neighbor] = new_dist
                prev[neighbor] = curr
                heapq.heappush(pq, (new_dist, neighbor))

    if target_id not in dist:
        return None

    # Reconstruct path from target back to source
    path: list[str] = []
    curr_node = target_id
    while curr_node != source_id:
        path.append(curr_node)
        curr_node = prev[curr_node]
    path.append(source_id)
    path.reverse()

    total_weight = dist[target_id]
    probability = round(math.exp(-total_weight), 4)

    return PathResult(
        nodes=path,
        probability=probability,
        total_weight=round(total_weight, 5),
    )


def attack_paths_to_critical(
    network: Network, source_id: str
) -> list[PathResult]:
    """Discover most probable attack paths from source_id to all critical assets.

    Contract:
      - Critical assets defined as nodes with criticality >= network.meta.critical_threshold.
      - Returns list of PathResult objects sorted by highest probability descending.
    """
    if source_id not in network.nodes:
        return []

    threshold = network.meta.critical_threshold
    critical_targets = [
        nid
        for nid, node in network.nodes.items()
        if node.criticality >= threshold and nid != source_id
    ]

    paths: list[PathResult] = []
    for target in critical_targets:
        res = most_probable_path(network, source_id, target)
        if res is not None:
            paths.append(res)

    # Sort by probability descending, then lowest weight, then path node names
    paths.sort(key=lambda p: (-p.probability, p.total_weight, p.nodes))
    return paths


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
    # Active incidents associated with the compromised nodes
    active_incidents = [
        inc for inc in network.incidents.values() if inc.node_id in compromised_ids
    ]
    if not active_incidents:
        # Fallback to all incidents if none explicitly match compromised_ids
        active_incidents = list(network.incidents.values())

    risk_before = sum(compute_score(network, inc).score for inc in active_incidents)
    risk_before = round(risk_before, 4)

    # Collect critical attack paths from all compromised nodes
    all_critical_paths: list[PathResult] = []
    candidate_node_ids: set[str] = set()

    for comp_id in compromised_ids:
        c_paths = attack_paths_to_critical(network, comp_id)
        all_critical_paths.extend(c_paths)
        for p in c_paths:
            # Candidate isolation nodes: intermediate or target nodes (not the source itself)
            for nid in p.nodes:
                if nid not in compromised_ids:
                    candidate_node_ids.add(nid)

    # If no paths found, evaluate any nodes in blast radius
    if not candidate_node_ids:
        for comp_id in compromised_ids:
            b = blast_radius(network, comp_id)
            for nid in b:
                if nid not in compromised_ids:
                    candidate_node_ids.add(nid)

    options: list[ContainmentOption] = []

    for candidate_id in candidate_node_ids:
        candidate_node = network.get_node(candidate_id)
        if not candidate_node:
            continue

        disruption_cost = candidate_node.criticality

        # Count critical attack paths that pass through this candidate
        paths_covered = sum(
            1 for p in all_critical_paths if candidate_id in p.nodes[1:]
        )

        # Isolate candidate node and recompute risk
        isolated_net = network.without_node(candidate_id)
        risk_after = sum(
            compute_score(isolated_net, inc).score for inc in active_incidents
        )
        risk_after = round(risk_after, 4)

        if risk_before > 0:
            risk_removed_pct = round(((risk_before - risk_after) / risk_before) * 100, 2)
        else:
            risk_removed_pct = 0.0

        options.append(
            ContainmentOption(
                node_id=candidate_id,
                paths_covered=paths_covered,
                risk_before=risk_before,
                risk_after=risk_after,
                risk_removed_pct=risk_removed_pct,
                disruption_cost=disruption_cost,
            )
        )

    # Sort options: highest risk reduction first, then most paths covered, then lowest disruption cost
    options.sort(
        key=lambda opt: (-opt.risk_removed_pct, -opt.paths_covered, opt.disruption_cost, opt.node_id)
    )

    return options
