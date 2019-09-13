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

    def load(self, schema):
        for name, params in schema.get('repositories').items():
            self.append(Repository(name=name, **params))

        for name, params in schema.get('mirrors').items():
            self.append(Mirror(name=name, **params))

        for name, params in schema.get('snapshots').items():
            action = params.pop('type')
            if action == 'create' and params.get('repository') is not None:
                self.append(SnapshotRepository(name=name, **params))
            elif action == 'create' and params.get('mirror') is not None:
                self.append(SnapshotMirror(name=name, **params))
            elif action == 'filter':
                self.append(SnapshotFilter(name=name, **params))
            elif action == 'merge':
                self.append(SnapshotMerge(name=name, **params))

