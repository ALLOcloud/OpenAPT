from collections import defaultdict
from allocloud.openapt.errors import CircularDependencyException

class Graph():
    def __init__(self):
        self.edges = EdgeCollection()

    def add_dependency(self, source, dependency):
        self.edges.append(source, dependency)

    def resolve(self, entities):
        # First we get a list of all entity which are not a dependency of another entity
        edges = self.edges.copy()
        root_entities = list(filter(lambda entity: edges.has_dependency(entity) is None, entities))
        sorted_entities = []
        while len(root_entities):
            entity = root_entities.pop()
            sorted_entities.append(entity)
            for source, dependency in edges.copy():
                if source != entity:
                    continue

                edges.remove(source, dependency)
                if not edges.has_dependency(dependency):
                    root_entities.append(dependency)

        if not edges.empty():
            raise CircularDependencyException()

        sorted_entities.sort(key=lambda entity: entity.priority)
        sorted_entities.reverse()
        return sorted_entities

class EdgeCollection():
    def __init__(self, edges=[]):
        self.edges = edges

    def __iter__(self):
        return self.edges.__iter__()

    def __next__(self):
        return self.edges.__next__()

    def empty(self):
        return len(self.edges) <= 0

    def append(self, source, dependency):
        self.edges.append((source, dependency))

    def remove(self, source, dependency):
        self.edges.remove((source, dependency))

    def has_dependency(self, entity):
        try:
            next((source, dependency) for source, dependency in self.edges if dependency == entity)
            return True
        except StopIteration:
            return None

    def copy(self):
        return EdgeCollection(self.edges.copy())


