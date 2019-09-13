from typing import List, Optional
from dataclasses import dataclass, field

@dataclass
class Repository():
    name: str
    comment: Optional[str] = None
    component: Optional[str] = None
    distribution: Optional[str] = None
    architectures: Optional[List[str]] = None

@dataclass
class Mirror():
    name: str
    archive: str
    distribution: Optional[str] = None
    components: Optional[List[str]] = None
    architectures: Optional[List[str]] = None
    filter: Optional[str] = None
    filterWithDeps: bool = False
    withSources: bool = False
    withUdebs: bool = False

@dataclass
class Snapshot():
    name: str

    def __post_init__(type=None):
        print(type)

@dataclass
class SnapshotRepository(Snapshot):
    repository: str
    architectures: Optional[List[str]] = None

@dataclass
class SnapshotMirror(Snapshot):
    mirror: str
    architectures: Optional[List[str]] = None
