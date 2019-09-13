import json
from argparse import ArgumentParser
from allocloud.openapt.models import Repository, Mirror, SnapshotRepository, SnapshotMirror

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
        'schema',
        type=str,
        metavar='<schema>',
    )
    args = vars(parser.parse_args())

    schema = None
    with open(args.get('schema')) as f:
        schema = json.loads(f.read())

    # TODO validate json

    entities = []

    for name, params in schema.get('repositories').items():
        entities.append(Repository(name=name, **params))

    for name, params in schema.get('mirrors').items():
        entities.append(Mirror(name=name, **params))

    for name, params in schema.get('snapshots').items():
        action = params.pop('type')
        if action == 'create' and params.get('repository') is not None:
            entities.append(SnapshotRepository(name=name, **params))
        elif action == 'create' and params.get('mirror') is not None:
            entities.append(SnapshotMirror(name=name, **params))

    print(entities)

if __name__ == '__main__':
    main()
