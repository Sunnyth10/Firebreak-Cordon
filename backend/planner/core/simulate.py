"""Incident response strategy simulation engine (Phase 5).

Simulates and compares response outcomes under FCFS, Severity-Only, and Graph-Aware policies.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING, Any

from .models import Incident
from .scoring import compute_score

if TYPE_CHECKING:
    from .graph import Network


def _simulate_strategy(
    strategy: str,
    network: Network,
    incidents: list[Incident],
    seed: int,
) -> dict[str, Any]:
    """Execute a discrete time-step simulation for a single containment strategy."""
    if not incidents:
        return {"total_damage": 0.0, "handled_order": []}

    rng = random.Random(seed)
    active_incidents = list(incidents)
    handled_order: list[str] = []
    total_damage = 0.0
    current_net = network

    while active_incidents:
        # 1. Accrue damage from all currently uncontained incidents in this round
        for inc in active_incidents:
            sb = compute_score(current_net, inc)
            # Add small deterministic stochastic factor around 1.0 (+/- 5%)
            jitter = rng.uniform(0.95, 1.05)
            round_damage = sb.severity * sb.impact * jitter
            total_damage += round_damage

        # 2. Select the next incident to handle based on the strategy policy
        if strategy == "fcfs":
            # Earliest timestamp first
            selected = min(
                active_incidents,
                key=lambda inc: (inc.timestamp, inc.id),
            )
        elif strategy == "severity_only":
            # Highest raw severity first, breaking ties with earlier timestamp
            selected = max(
                active_incidents,
                key=lambda inc: (inc.severity, -hash(inc.timestamp) if False else (1, inc.timestamp)),
            )
            # Standard python sort key for max: (severity, -timestamp is not valid for str)
            # So sort by (inc.severity descending, inc.timestamp ascending)
            sorted_candidates = sorted(
                active_incidents,
                key=lambda inc: (-inc.severity, inc.timestamp, inc.id),
            )
            selected = sorted_candidates[0]
        elif strategy == "graph_aware":
            # Dynamic graph priority score descending, breaking ties with earlier timestamp
            scored_candidates = [
                (compute_score(current_net, inc).score, inc)
                for inc in active_incidents
            ]
            scored_candidates.sort(
                key=lambda item: (-item[0], item[1].timestamp, item[1].id)
            )
            selected = scored_candidates[0][1]
        else:
            raise ValueError(f"Unknown strategy: '{strategy}'")

        # 3. Contain/mitigate the selected incident
        handled_order.append(selected.id)
        active_incidents.remove(selected)

        # In graph-aware strategy, isolate the contained node from network attack edges
        if strategy == "graph_aware":
            current_net = current_net.without_node(selected.node_id)

    return {
        "total_damage": round(total_damage, 2),
        "handled_order": handled_order,
    }


def run_strategies(
    network: Network, incidents: list[Incident], seed: int = 42
) -> dict[str, dict[str, Any]]:
    """Simulate incident response across three distinct prioritization strategies.

    Contract:
      - Deterministic: uses the provided integer seed for all stochastic events.
      - Strategies:
          1. "fcfs": Handled in strict order of incident timestamp.
          2. "severity_only": Handled by highest raw severity descending.
          3. "graph_aware": Handled by dynamically recomputed graph priority score.
      - Returns mapping:
          {
              "fcfs": {"total_damage": float, "handled_order": list[str]},
              "severity_only": {"total_damage": float, "handled_order": list[str]},
              "graph_aware": {"total_damage": float, "handled_order": list[str]}
          }
    """
    strategies = ["fcfs", "severity_only", "graph_aware"]
    results: dict[str, dict[str, Any]] = {}

    for strat in strategies:
        # Each strategy receives the same base seed for fair comparison
        results[strat] = _simulate_strategy(
            strategy=strat,
            network=network,
            incidents=incidents,
            seed=seed,
        )

    return results
