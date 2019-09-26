import json
import logging
from argparse import ArgumentParser
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
    Context,
)

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
        metavar='<aptly config>',
        required=False,
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=False,
        required=False,
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

    # TODO validate json

    entities = EntityCollection()
    entities.load(schema)

    context = Context(config=args.get('config'), dry_run=args.get('dry_run'))

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

        ordered_entities = graph.resolve(entities)
        for entity in ordered_entities:
            entity.run(context)

    except OAException as oae:
        print(oae)

if __name__ == '__main__':
    main()
