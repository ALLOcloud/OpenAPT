from typing import List, Optional
from dataclasses import dataclass, field
from allocloud.openapt.errors import EntityNotFoundException

@dataclass
class Entity():
    name: str

    @property
    def priority(self):
        return -1

@dataclass
class Repository(Entity):
    comment: Optional[str] = None
    component: Optional[str] = None
    distribution: Optional[str] = None
    architectures: Optional[List[str]] = None

    @property
    def priority(self):
        return 4

@dataclass
class Mirror(Entity):
    archive: str
    distribution: Optional[str] = None
    components: Optional[List[str]] = None
    architectures: Optional[List[str]] = None
    filter: Optional[str] = None
    filterWithDeps: bool = False
    withSources: bool = False
    withUdebs: bool = False

    @property
    def priority(self):
        return 3

@dataclass
class Snapshot(Entity):

    @property
    def priority(self):
        return 2

@dataclass
class SnapshotRepository(Snapshot):
    repository: str
    architectures: Optional[List[str]] = None

@dataclass
class SnapshotMirror(Snapshot):
    mirror: str
    architectures: Optional[List[str]] = None

@dataclass
class SnapshotMerge(Snapshot):
    sources: List[str]
    architectures: Optional[List[str]] = None
    latest: bool = False
    noRemove: bool = False

@dataclass
class SnapshotFilter(Snapshot):
    source: str
    filter: str
    architectures: Optional[List[str]] = None
    withDeps: bool = False

class EntityCollection(list):
    def search(self, name, classinfo):
        try:
            return next(entity for entity in self if isinstance(entity, classinfo) and entity.name == name)
        except StopIteration:
            raise EntityNotFoundException()
