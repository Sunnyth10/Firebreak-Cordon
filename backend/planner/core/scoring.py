"""Priority scoring and incident queue stub (Phase 2 contract).

Computes explainable incident scores and maintains a versioned max-heap queue.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import Incident, ScoreBreakdown

if TYPE_CHECKING:
    from .graph import Network


def compute_score(network: Network, incident: Incident) -> ScoreBreakdown:
    """Calculate the transparent, explainable priority score for an incident.

    Contract:
      - own_criticality: node.criticality
      - blast: blast_radius(network, incident.node_id)
      - reachable_weighted_criticality = sum(crit(v) * reach_prob(v)) for v in blast
      - impact = own_criticality + reachable_weighted_criticality
      - score = severity * confidence * impact
      - Returns ScoreBreakdown dataclass.
    """
    raise NotImplementedError("compute_score is scheduled for Phase 2 implementation.")


class IncidentQueue:
    """Max-heap priority queue with lazy updates and version tracking."""

    def __init__(self) -> None:
        """Initialize empty priority queue structures."""
        raise NotImplementedError("IncidentQueue.__init__ is scheduled for Phase 2 implementation.")

    def push(self, incident: Incident, score: float) -> None:
        """Insert a new incident with its priority score."""
        raise NotImplementedError("IncidentQueue.push is scheduled for Phase 2 implementation.")

    def update(self, incident_id: str, new_score: float) -> None:
        """Update the score of an incident lazily via version increment."""
        raise NotImplementedError("IncidentQueue.update is scheduled for Phase 2 implementation.")

    def pop(self) -> tuple[Incident, float]:
        """Remove and return the highest priority (incident, score) tuple."""
        raise NotImplementedError("IncidentQueue.pop is scheduled for Phase 2 implementation.")

    def peek(self) -> tuple[Incident, float] | None:
        """Return the highest priority (incident, score) without removing it."""
        raise NotImplementedError("IncidentQueue.peek is scheduled for Phase 2 implementation.")

    def ranked(self) -> list[tuple[Incident, float]]:
        """Return all active incidents sorted from highest to lowest priority."""
        raise NotImplementedError("IncidentQueue.ranked is scheduled for Phase 2 implementation.")

    def __len__(self) -> int:
        """Return the count of active (non-stale) incidents in the queue."""
        raise NotImplementedError("IncidentQueue.__len__ is scheduled for Phase 2 implementation.")
