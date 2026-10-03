"""Priority scoring and incident queue engine (Phase 2).

Computes explainable incident scores and maintains a versioned max-heap queue.
"""

from __future__ import annotations

import heapq
from typing import TYPE_CHECKING

from .blast import blast_radius
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
    node = network.get_node(incident.node_id)
    if not node:
        raise ValueError(f"Incident references non-existent node: '{incident.node_id}'")

    own_criticality = node.criticality
    blast = blast_radius(network, incident.node_id)

    reachable_weighted_criticality = 0.0
    for target_id, data in blast.items():
        target_node = network.get_node(target_id)
        if target_node:
            reachable_weighted_criticality += target_node.criticality * float(data["reach_probability"])

    reachable_weighted_criticality = round(reachable_weighted_criticality, 4)
    impact = round(own_criticality + reachable_weighted_criticality, 4)
    score = round(incident.severity * incident.confidence * impact, 4)

    return ScoreBreakdown(
        severity=incident.severity,
        confidence=incident.confidence,
        own_criticality=own_criticality,
        reachable_weighted_criticality=reachable_weighted_criticality,
        impact=impact,
        score=score,
    )


class IncidentQueue:
    """Max-heap priority queue with lazy updates and version tracking."""

    def __init__(self) -> None:
        """Initialize empty priority queue structures."""
        self._heap: list[tuple[float, str, str, int]] = []
        self._incidents: dict[str, Incident] = {}
        self._scores: dict[str, float] = {}
        self._versions: dict[str, int] = {}

    def push(self, incident: Incident, score: float) -> None:
        """Insert a new incident with its priority score."""
        incident_id = incident.id
        version = self._versions.get(incident_id, 0) + 1
        self._versions[incident_id] = version
        self._incidents[incident_id] = incident
        self._scores[incident_id] = score
        # Python min-heap uses -score for max-heap behavior;
        # earlier timestamp breaks score ties deterministically.
        heapq.heappush(self._heap, (-score, incident.timestamp, incident_id, version))

    def update(self, incident_id: str, new_score: float) -> None:
        """Update the score of an incident lazily via version increment."""
        if incident_id not in self._incidents:
            raise KeyError(f"Incident '{incident_id}' not found in queue.")
        incident = self._incidents[incident_id]
        version = self._versions[incident_id] + 1
        self._versions[incident_id] = version
        self._scores[incident_id] = new_score
        heapq.heappush(self._heap, (-new_score, incident.timestamp, incident_id, version))

    def _clean_top(self) -> None:
        """Discard stale/deleted entries from the top of the heap."""
        while self._heap:
            neg_score, ts, iid, ver = self._heap[0]
            if iid not in self._incidents or ver != self._versions.get(iid):
                heapq.heappop(self._heap)
            else:
                break

    def pop(self) -> tuple[Incident, float]:
        """Remove and return the highest priority (incident, score) tuple."""
        self._clean_top()
        if not self._heap:
            raise IndexError("pop from an empty IncidentQueue")
        neg_score, ts, iid, ver = heapq.heappop(self._heap)
        incident = self._incidents.pop(iid)
        score = self._scores.pop(iid)
        del self._versions[iid]
        return incident, score

    def peek(self) -> tuple[Incident, float] | None:
        """Return the highest priority (incident, score) without removing it."""
        self._clean_top()
        if not self._heap:
            return None
        neg_score, ts, iid, ver = self._heap[0]
        return self._incidents[iid], self._scores[iid]

    def ranked(self) -> list[tuple[Incident, float]]:
        """Return all active incidents sorted from highest to lowest priority."""
        self._clean_top()
        sorted_incidents = sorted(
            self._incidents.values(),
            key=lambda inc: (-self._scores[inc.id], inc.timestamp, inc.id),
        )
        return [(inc, self._scores[inc.id]) for inc in sorted_incidents]

    def __len__(self) -> int:
        """Return the count of active (non-stale) incidents in the queue."""
        return len(self._incidents)

    def __contains__(self, incident_id: str) -> bool:
        """Check if an incident ID is active in the queue."""
        return incident_id in self._incidents

    def get_score(self, incident_id: str) -> float | None:
        """Get the current score of an incident in the queue."""
        return self._scores.get(incident_id)
