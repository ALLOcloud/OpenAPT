import unittest.mock
import logging
import sys
import os
import io
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Mapping

import pytest

from allocloud.openapt.models import LOGGER, Context, NameFormatter
from allocloud.openapt.__main__ import main

@dataclass
class Case:
    input_path: str
    expected_output: str
    options: Mapping[str, str]

def cases(basedir):
    _cases = []
    for subdir, dirs, _ in os.walk(basedir):
        if Path(subdir) == basedir:
            for _dir in dirs:
                _options_path = basedir / _dir / 'options.json'
                _input_path = basedir / _dir / 'input.json'
                _output_path = basedir / _dir / 'output'

                _options = {}
                if _options_path.exists():
                    with open(_options_path, 'r') as file:
                        _options = json.load(file)

                with open(_output_path, 'r') as file:
                    _output = file.read()

                _case = Case(input_path=str(_input_path), expected_output=_output, options=_options)
                _cases.append(_case)
    return _cases

CASES = cases(Path(__file__).parent / 'input_output_cases')

@pytest.mark.parametrize('case', CASES)
def test_input_output(case):
    with unittest.mock.patch('allocloud.openapt.__main__.Context') as MockContext:
        context = Context(
            config=None,
            dry_run=True,
            formats={
                'snapshot': case.options.get('--snapshot-subst', '{name}'),
            },
        )
        MockContext.return_value = context

        formatter = NameFormatter()
        case.expected_output = formatter.format(
            case.expected_output,
            now=context.now,
            random=context.random,
        )

        log_string = io.StringIO()
        handler = logging.StreamHandler(log_string)
        handler.setLevel(logging.DEBUG)
        LOGGER.setLevel(logging.DEBUG)

        LOGGER.addHandler(handler)
        sys.argv.append(case.input_path)
        try:
            main()
        finally:
            sys.argv.pop()
            LOGGER.removeHandler(handler)

        log_contents = log_string.getvalue()
        log_string.close()

        assert log_contents == case.expected_output
