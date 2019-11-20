import unittest.mock
import logging
import tempfile
import pkgutil
import os
import io
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Mapping

import pytest

from allocloud.openapt.models import Context, NameFormatter
from allocloud.openapt import create_stream_handler, setup_logging, run

@dataclass
class Case:
    setup: List[List[str]]
    input_path: str
    options: Mapping[str, str]
    expected_output: str

def list_dirs(basedir):
    for subdir, dirs, _ in os.walk(basedir):
        if Path(subdir) == basedir:
            for _dir in dirs:
                yield _dir

def cases(basedir):
    _cases = []
    for _dir in list_dirs(basedir):
        _case_dir = basedir / _dir
        _setup_path = _case_dir / 'setup.json'
        _input_path = _case_dir / 'input.json'

        _setup = []
        if _setup_path.exists():
            with open(_setup_path, 'r') as file:
                _setup = json.load(file)

        for __dir in list_dirs(_case_dir):
            _options_path = _case_dir / __dir / 'options.json'
            _output_path = _case_dir / __dir / 'output'

            _options = {}
            if _options_path.exists():
                with open(_options_path, 'r') as file:
                    _options = json.load(file)

            with open(_output_path, 'r') as file:
                _output = file.read()

            _case = Case(
                setup=_setup,
                input_path=str(_input_path),
                options=_options,
                expected_output=_output,
            )
            _cases.append(_case)
    return _cases

CASES = cases(Path(__file__).parent / 'e2e' / 'cases')
APTLY_CONF_TEMPLATE = json.loads(pkgutil.get_data('e2e', 'aptly.conf'))

@pytest.mark.parametrize('case', CASES)
def test_e2e(case, caplog):
    setup_logging()
    caplog.set_level(logging.DEBUG)

    with tempfile.TemporaryDirectory() as root_dir:
        with open(Path(root_dir) / 'aptly.conf', 'w+') as f:
            f.write(json.dumps({**APTLY_CONF_TEMPLATE, 'rootDir': root_dir}))

        context = Context(
            config=f.name,
            formats={
                'snapshot': case.options.get('--snapshot-subst', '{name}'),
            },
        )
        formatter = NameFormatter()
        case.expected_output = formatter.format(
            case.expected_output,
            now=context.now,
            random=context.random,
        )

        for step in case.setup:
            assert context.execute(step, 0)

        with unittest.mock.patch('allocloud.openapt.Context') as MockContext:
            MockContext.return_value = context

            log_string = io.StringIO()
            handler = create_stream_handler(log_string, logging.INFO, max_level=logging.INFO)

            logger = logging.getLogger()
            logger.addHandler(handler)
            try:
                run(case.input_path, limit=case.options.get('--limit'))
            finally:
                logger.removeHandler(handler)

            log_contents = log_string.getvalue()
            log_contents = log_contents.replace(f' -config={f.name}', '')
            log_string.close()

            assert log_contents == case.expected_output
