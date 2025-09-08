from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class Class:
    name: str
    attributes: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)


@dataclass
class Relation:
    source: str  # class name
    target: str  # class name
    type: str  # e.g., "association", "inheritance", "aggregation", "composition", "dependency"
