import logging
import errno
import io
import select
from subprocess import Popen, PIPE
from contextlib import contextmanager

from allocloud.openapt.logging import create_stream_handler


LOGGER = logging.getLogger(__name__)


def run_command(command, log_output=False):
    with Popen(command, stdout=PIPE, stderr=PIPE) as process:
        files = [process.stdout, process.stderr]
        while process.poll() is None:
            while files:
                try:
                    streams, _, _ = select.select(files, [], [])
                except select.error as err:
                    if err.args[0] == errno.EINTR:
                        continue
                    raise

                if process.stderr in streams:
                    output = process.stderr.readline().decode()
                    if not output:
                        process.stderr.close()
                        files.remove(process.stderr)
                    elif log_output:
                        LOGGER.error(output.rstrip('\n'))

                if process.stdout in streams:
                    output = process.stdout.readline().decode()
                    if not output:
                        process.stdout.close()
                        files.remove(process.stdout)
                    elif log_output:
                        LOGGER.debug(output.rstrip('\n'))
    return process

@contextmanager
def capture_output():
    LOGGER.propagate = False
    log_string = io.StringIO()
    handler = create_stream_handler(log_string, logging.DEBUG, max_level=logging.DEBUG)
    bk_handlers = LOGGER.handlers
    LOGGER.handlers = [handler]

    try:
        yield log_string
    finally:
        log_string.close()
        LOGGER.handlers = bk_handlers
        LOGGER.propagate = True
