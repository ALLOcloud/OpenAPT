import sys
import logging
from argparse import ArgumentParser

from allocloud.openapt.errors import SchemaParseException, OAException
from allocloud.openapt.logging import setup_logging
from . import run


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
        '--update',
        action='store_true',
        default=False,
        required=False,
        help='update package lists from upstream mirrors',
    )
    parser.add_argument(
        '--snapshot-subst',
        required=False,
        metavar='<template>',
        help='formating string for snapshots (e.g. "{now:date:%%Y%%d%%m_%%H%%M%%S}_{random:.8s}_{name}")',
    )
    parser.add_argument(
        '--limit',
        dest='limits',
        action='append',
        required=False,
        metavar='<limit-description>',
        help='limit string (e.g. "publishing:mydistro")',
    )
    parser.add_argument(
        'schema',
        type=str,
        metavar='<schema>',
    )
    args = vars(parser.parse_args())

    setup_logging(**args)

    try:
        run(**args)
    except SchemaParseException as spe:
        LOGGER.error(spe)
        LOGGER.error(spe.errors[0].message)
        sys.exit(1)
    except OAException as oae:
        LOGGER.error(oae)
        sys.exit(1)

if __name__ == '__main__':
    main()
