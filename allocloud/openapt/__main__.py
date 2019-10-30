import sys
import json
import logging
from argparse import ArgumentParser
from pkg_resources import resource_string
from jsonschema import Draft4Validator
from allocloud.openapt.errors import OAException
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
    Context,
)

LOGGER = logging.getLogger(__name__)

def main():
    parser = ArgumentParser(description='OpenAPT Aptly implementation.')
    parser.add_argument(
        '--debug',
        action='store_true',
        default=False,
        required=False,
    )
    parser.add_argument(
        '--config',
        type=str,
        metavar='<file>',
        required=False,
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=False,
        required=False,
    )
    parser.add_argument(
        '--snapshot-subst',
        required=False,
        metavar='<template>',
        help='Formating string for snapshots (e.g. "{now:date:%%Y%%d%%m_%%H%%M%%S}_{random:.8s}_{name}")',
    )
    parser.add_argument(
        'schema',
        type=str,
        metavar='<schema>',
    )
    args = vars(parser.parse_args())

    logging.basicConfig(level=logging.DEBUG if args['debug'] else logging.WARNING, format='%(message)s')

    schema = None
    with open(args.get('schema')) as f:
        schema = json.loads(f.read())

    validator = Draft4Validator(json.loads(resource_string(__name__, 'meta-schema.json')))
    failure = False
    for error in validator.iter_errors(schema):
        LOGGER.error(error.message)
        failure = True

    if failure:
        sys.exit(1)

    context = Context(
        config=args.get('config'),
        dry_run=args.get('dry_run'),
        formats={
            'snapshot': args.get('snapshot_subst') or '{name}',
        }
    )

    entities = EntityCollection()
    entities.load(schema, context)

    # Generate dependency graph
    graph = Graph()
    try:
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
            elif isinstance(entity, (Mirror, Repository)):
                pass
            else:
                raise RuntimeError('unhandled entity type: {}'.format(type(entity)))

        ordered_entities = graph.resolve(entities)
        for entity in ordered_entities:
            entity.run()

    except OAException as oae:
        LOGGER.error(oae)
        sys.exit(1)

if __name__ == '__main__':
    main()
