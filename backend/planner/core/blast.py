"""Blast radius calculation engine (Phase 1).

Computes reachable systems over network edges using BFS for hop distance
and optimal path probability product via Dijkstra on additive weights w = -ln(p).
"""

from __future__ import annotations

import heapq
import math
from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .graph import Network


def blast_radius(
    network: Network, source_id: str
) -> dict[str, dict[str, int | float]]:
    """Compute reachable systems from source_id over directed network edges.

    Contract:
      - Traverses only edges where kind == 'network'.
      - For each reachable node v (excluding source_id):
          - hops: minimum edge count from source_id to v (via BFS).
          - reach_probability: maximum product of edge probabilities along any
            directed network path from source_id to v (w = -ln(p)).
      - Returns mapping:
          {
              "node_id": {
                  "hops": int,
                  "reach_probability": float
              }
          }
      - If source has no outgoing edges or is not found, returns empty dict {}.
    """
    if source_id not in network.nodes:
        return {}

    # 1. BFS to compute minimum hop count
    hops: dict[str, int] = {}
    queue: deque[tuple[str, int]] = deque([(source_id, 0)])
    visited_bfs: set[str] = {source_id}

    while queue:
        curr, h = queue.popleft()
        if curr != source_id:
            hops[curr] = h

        for target, _ in network.network_adj.get(curr, []):
            if target not in visited_bfs:
                visited_bfs.add(target)
                queue.append((target, h + 1))

    # If no nodes reachable, blast radius is empty
    if not hops:
        return {}

    # 2. Dijkstra to find maximum probability path:
    # Since p in (0, 1.0], w = -ln(p) >= 0. Minimizing sum(-ln(p)) maximizes prod(p).
    dist: dict[str, float] = {source_id: 0.0}
    pq: list[tuple[float, str]] = [(0.0, source_id)]

    while pq:
        d, curr = heapq.heappop(pq)
        if d > dist.get(curr, float("inf")):
            continue

        for target, prob in network.network_adj.get(curr, []):
            w = -math.log(prob)
            new_dist = d + w
            if new_dist < dist.get(target, float("inf")):
                dist[target] = new_dist
                heapq.heappush(pq, (new_dist, target))

    # 3. Assemble blast radius mapping
    result: dict[str, dict[str, int | float]] = {}
    for target, hop_count in hops.items():
        min_weight = dist[target]
        reach_prob = round(math.exp(-min_weight), 4)
        result[target] = {
            "hops": hop_count,
            "reach_probability": reach_prob,
        }

    return result
