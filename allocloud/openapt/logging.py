import logging
import sys


class LogLevelFilter:
    def __init__(self, level):
        self.level = level

    def filter(self, record):
        return record.levelno <= self.level


def create_stream_handler(stream, level, fmt='%(message)s', max_level=None):
    handler = logging.StreamHandler(stream)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(fmt))
    if max_level:
        handler.addFilter(LogLevelFilter(max_level))
    return handler


def setup_logging(dry_run=False, debug=False, **kwargs):
    level = logging.WARNING
    if dry_run:
        level = logging.INFO
    if debug:
        level = logging.DEBUG

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    root.addHandler(create_stream_handler(sys.stdout, level, max_level=logging.INFO))
    root.addHandler(create_stream_handler(sys.stderr, logging.WARNING))
