import unittest.mock
import logging
import sys
import shutil
import subprocess
import os
import io
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Mapping

import pytest

from allocloud.openapt.models import LOGGER, Context, NameFormatter
from allocloud.openapt.__main__ import main

class LogLevelFilter:
    def __init__(self, level):
        self._level = level

    def filter(self, record):
        return record.levelno <= self._level

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
    def wrap_context_execute(func):
        def wrapped(_args, *args, **kwargs):
            if _args[:2] == ['repo', 'show']:
                return False
            return func(_args, *args, **kwargs)
        return wrapped

    context = Context(
        config=None,
        dry_run=shutil.which('aptly') is None,
        formats={
            'snapshot': case.options.get('--snapshot-subst', '{name}'),
        },
    )
    context.execute = wrap_context_execute(context.execute)

    if not context.dry_run:
        subprocess.run(['equivs-build', '/app/allocloud-test'], check=True)
        subprocess.run(['sudo', 'rm', '-rf', '/aptly'], check=True)
        subprocess.run(['sudo', 'mkdir', '/aptly'], check=True)
        subprocess.run(['sudo', 'chmod', '777', '/aptly'], check=True)
        assert context.execute(['repo', 'create', 'allocloud'], 0)
        assert context.execute(['repo', 'add', 'allocloud', '/app/allocloud-test_1.0_all.deb'], 0)
        subprocess.run(['rm', '-rf', '/app/allocloud-test_1.0_all.deb'], check=True)

    formatter = NameFormatter()
    case.expected_output = formatter.format(
        case.expected_output,
        now=context.now,
        random=context.random,
    )

    with unittest.mock.patch('allocloud.openapt.__main__.Context') as MockContext:
        MockContext.return_value = context

        log_string = io.StringIO()
        handler = logging.StreamHandler(log_string)
        handler.setLevel(logging.INFO)
        handler.addFilter(LogLevelFilter(logging.INFO))
        LOGGER.setLevel(logging.DEBUG)

        LOGGER.addHandler(handler)
        sys.argv.append(case.input_path)
        try:
            main()
        finally:
            sys.argv.pop()
            LOGGER.removeHandler(handler)
            LOGGER.setLevel(logging.NOTSET)

        log_contents = log_string.getvalue()
        log_string.close()

        assert log_contents == case.expected_output
