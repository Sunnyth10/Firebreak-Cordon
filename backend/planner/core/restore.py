"""Dependency cycle detection and restore order stub (Phase 4 contract).

Traverses dependency edges using iterative DFS to identify safe restore sequences
and detect circular dependency deadlocks.
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
    raise NotImplementedError("restore_order is scheduled for Phase 4 implementation.")
