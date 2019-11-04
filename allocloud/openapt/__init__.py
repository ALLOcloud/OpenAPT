import json
from pkg_resources import resource_string

from jsonschema import Draft4Validator

from allocloud.openapt.errors import SchemaParseException
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


META_SCHEMA = json.loads(resource_string(__name__, 'meta-schema.json'))


def run(schema, config=None, snapshot_subst=None, dry_run=False, **kwargs):
    with open(schema) as f:
        _schema = json.loads(f.read())

    validator = Draft4Validator(META_SCHEMA)
    errors = list(validator.iter_errors(_schema))
    if errors:
        raise SchemaParseException(errors)

    context = Context(
        config=config,
        dry_run=dry_run,
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
            graph.add_dependency(entity, entities.search(entity.to, Snapshot))
        elif isinstance(entity, Publishing):
            graph.add_dependency(entity, entities.search(entity.snapshot, Snapshot))
        elif isinstance(entity, (Mirror, Repository)):
            pass
        else:
            raise RuntimeError('unhandled entity type: {}'.format(type(entity)))

    ordered_entities = graph.resolve(entities)
    for entity in ordered_entities:
        entity.run()
