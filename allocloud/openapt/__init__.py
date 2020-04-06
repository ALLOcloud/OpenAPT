import sys
import json
import yaml

from allocloud.openapt.specs import validate_schema
from allocloud.openapt.dependency import Graph
from allocloud.openapt.models import (
    EntityCollection,
    Repository,
    Mirror,
    Snapshot,
    SnapshotRepository,
    SnapshotMirror,
    SnapshotFilter,
    SnapshotMerge,
    SnapshotPull,
    Publishing,
    Context,
)


def class_for(keyword):
    if keyword == 'repository':
        return Repository
    if keyword == 'mirror':
        return Mirror
    if keyword == 'snapshot':
        return Snapshot
    if keyword == 'publishing':
        return Publishing
    raise ValueError('unknown keyword "{}"'.format(keyword))


# pylint:disable=too-many-locals
def run(schema, config=None, snapshot_subst=None, dry_run=False, update=False, limits=None, **kwargs):
    with open(schema) as f:
        _schema = yaml.load(f)

    validate_schema(_schema)

    context = Context(
        config=config,
        dry_run=dry_run,
        update=update,
        formats={
            'snapshot': snapshot_subst or '{name}',
        }
    )

    entities = EntityCollection()
    entities.load(_schema, context)

    # Generate dependency graph
    graph = Graph()
    for entity in entities:
        if isinstance(entity, SnapshotRepository):
            graph.add_dependency(entity, entities.search(entity.repository, Repository))
        elif isinstance(entity, SnapshotMirror):
            graph.add_dependency(entity, entities.search(entity.mirror, Mirror))
        elif isinstance(entity, SnapshotFilter):
            graph.add_dependency(entity, entities.search(entity.source, Snapshot))
        elif isinstance(entity, SnapshotMerge):
            for source in entity.sources:
                graph.add_dependency(entity, entities.search(source, Snapshot))
        elif isinstance(entity, SnapshotPull):
            graph.add_dependency(entity, entities.search(entity.source, Snapshot))
            graph.add_dependency(entity, entities.search(entity.recipient, Snapshot))
        elif isinstance(entity, Publishing):
            graph.add_dependency(entity, entities.search(entity.snapshot, Snapshot))
        elif isinstance(entity, (Mirror, Repository)):
            pass
        else:
            raise RuntimeError('unhandled entity type: {}'.format(type(entity)))

    ordered_entities = graph.resolve(
        entities,
        [entities.search(limit.split(':')[1], class_for(limit.split(':')[0])) for limit in limits or []]
    )

    for entity in ordered_entities:
        entity.run()
