import logging
import sys
import os
import io
from pathlib import Path

import pytest

from allocloud.openapt.models import LOGGER
from allocloud.openapt.__main__ import main

def cases(basedir):
    _cases = []
    for subdir, dirs, _ in os.walk(basedir):
        if Path(subdir) == basedir:
            for _dir in dirs:
                _input = str(basedir / _dir / 'input.json')
                with open(basedir / _dir / 'output', 'r') as file:
                    _output = file.read()
                _cases.append(tuple([_input, _output]))
    return _cases

CASES = cases(Path(__file__).parent / 'input_output_cases')

@pytest.mark.parametrize('test_input,expected_output', CASES)
def test_input_output(test_input, expected_output):
    log_string = io.StringIO()
    handler = logging.StreamHandler(log_string)
    handler.setLevel(logging.DEBUG)
    LOGGER.setLevel(logging.DEBUG)
    LOGGER.addHandler(handler)

    sys.argv.append(test_input)
    sys.argv.append('--dry-run')
    try:
        main()
    finally:
        LOGGER.removeHandler(handler)
        sys.argv.pop()
        sys.argv.pop()
        print(sys.argv)

    log_contents = log_string.getvalue()
    log_string.close()

    assert log_contents == expected_output
