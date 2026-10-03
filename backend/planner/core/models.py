"""Data models and enums for cyber incident planning."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class NodeType(str, Enum):
    """Allowed node asset types."""
    WEB = "web"
    APP = "app"
    DATABASE = "database"
    AUTH = "auth"
    BACKUP = "backup"
    ENDPOINT = "endpoint"
    PERIPHERAL = "peripheral"
    NETWORK = "network"


class NodeStatus(str, Enum):
    """Operational / compromise status of a node."""
    HEALTHY = "healthy"
    SUSPECTED = "suspected"
    COMPROMISED = "compromised"


class EdgeKind(str, Enum):
    """Classification of an edge relationship."""
    NETWORK = "network"
    DEPENDENCY = "dependency"


@dataclass(frozen=True)
class Node:
    """Represents a system asset in the network."""
    id: str
    name: str
    type: NodeType | str
    criticality: int
    status: NodeStatus | str = NodeStatus.HEALTHY

    def __post_init__(self) -> None:
        if isinstance(self.type, NodeType):
            object.__setattr__(self, "type", self.type.value)
        if isinstance(self.status, NodeStatus):
            object.__setattr__(self, "status", self.status.value)


@dataclass(frozen=True)
class Edge:
    """Represents a lateral network attack pivot or functional dependency."""
    id: str
    source: str
    target: str
    kind: EdgeKind | str
    probability: float | None = None

    def __post_init__(self) -> None:
        if isinstance(self.kind, EdgeKind):
            object.__setattr__(self, "kind", self.kind.value)


@dataclass(frozen=True)
class Incident:
    """Represents an active security alert on a specific node."""
    id: str
    node_id: str
    severity: int
    confidence: float
    timestamp: str


@dataclass(frozen=True)
class NetworkMeta:
    """Metadata settings for the network graph."""
    name: str = "Cyber Incident Network"
    critical_threshold: int = 8


@dataclass(frozen=True)
class ScoreBreakdown:
    """Explainable priority score components."""
    severity: int
    confidence: float
    own_criticality: int
    reachable_weighted_criticality: float
    impact: float
    score: float


@dataclass(frozen=True)
class PathResult:
    """Result of an attack path discovery query."""
    nodes: list[str]
    probability: float
    total_weight: float


@dataclass(frozen=True)
class ContainmentOption:
    """Candidate node isolation evaluation."""
    node_id: str
    paths_covered: int
    risk_before: float
    risk_after: float
    risk_removed_pct: float
    disruption_cost: int


@dataclass(frozen=True)
class RestoreResult:
    """Topological restoration order result or detected cycle."""
    ok: bool
    order: list[str] | None = None
    cycle: list[str] | None = None
    explanation: str | None = None
