"""Dependency cycle detection and topological restore order engine (Phase 4).

Traverses dependency edges using an iterative DFS (three-color state machine)
to identify safe system restoration sequences and detect circular dependency deadlocks
without recursion depth limits.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import RestoreResult

if TYPE_CHECKING:
    from .graph import Network


def restore_order(network: Network) -> RestoreResult:
    """Compute dependency-safe restoration order for all network nodes.

    Contract:
      - Traverses edges where kind == 'dependency'.
      - Semantics: For edge u -> v (u requires v), v MUST be restored before u.
      - Uses iterative DFS (three-color state) to avoid recursion depth limits.
      - If acyclic:
          returns RestoreResult(ok=True, order=[...], cycle=None, explanation="...")
          where all dependencies appear before dependent systems.
      - If cyclic:
          returns RestoreResult(ok=False, order=None, cycle=[...], explanation="...")
          where cycle identifies the circular dependency path.
    """
    # Node states: 0 = WHITE (unvisited), 1 = GRAY (on current DFS stack), 2 = BLACK (finished)
    color: dict[str, int] = {nid: 0 for nid in network.nodes}
    post_order: list[str] = []

    # Sort node ids for deterministic exploration order across runs
    node_ids = sorted(list(network.nodes.keys()))

    for root in node_ids:
        if color[root] != 0:
            continue

        # Iterative DFS stack: holds current path of active nodes
        stack: list[str] = [root]
        color[root] = 1
        edge_cursor: dict[str, int] = {root: 0}

        while stack:
            u = stack[-1]
            dependencies = network.dependency_adj.get(u, [])
            cursor = edge_cursor[u]

            if cursor < len(dependencies):
                v = dependencies[cursor]
                edge_cursor[u] = cursor + 1

                # If neighbor node is unknown (e.g. not in nodes dict), skip or track
                v_color = color.get(v, 0)

                if v_color == 1:
                    # GRAY: back-edge found -> cycle detected!
                    cycle_start = stack.index(v)
                    cycle = stack[cycle_start:] + [v]
                    return RestoreResult(
                        ok=False,
                        order=None,
                        cycle=cycle,
                        explanation=(
                            f"Circular dependency detected: {' -> '.join(cycle)}. "
                            "Restoration blocked due to dependency deadlock."
                        ),
                    )
                elif v_color == 0:
                    # WHITE: advance to dependent child
                    color[v] = 1
                    edge_cursor[v] = 0
                    stack.append(v)
            else:
                # All prerequisites of u have been explored and ordered
                stack.pop()
                color[u] = 2
                post_order.append(u)

    return RestoreResult(
        ok=True,
        order=post_order,
        cycle=None,
        explanation=(
            "Valid dependency-safe restoration order: all required systems "
            "are scheduled before the systems that depend upon them."
        ),
    )
