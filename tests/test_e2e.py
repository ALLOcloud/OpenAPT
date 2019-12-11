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

AptlyArgument = str
AptlyCommand = List[AptlyArgument]

@dataclass
class Case:
    name: str
    before: List[AptlyCommand]
    schema: str
    arguments: Mapping[str, str]
    expected_output: str

def list_dirs(basedir):
    for subdir, dirs, _ in os.walk(basedir):
        if Path(subdir) == basedir:
            for _dir in dirs:
                yield _dir

def collect_cases(base_dir):
    cases = []
    for case_dir in list_dirs(base_dir):
        with open(base_dir / case_dir / 'setup.json', 'r') as f:
            setup = json.load(f)

        with open(base_dir / case_dir / 'output.txt', 'r') as f:
            output = f.read()

        cases.append(
            Case(
                name=case_dir,
                before=setup.get('before', []),
                arguments=setup.get('arguments', {}),
                schema=str(base_dir / case_dir / setup.get('schema', 'schema.json')),
                expected_output=output,
            )
        )
    return cases

CASES = collect_cases(Path(__file__).parent / 'e2e' / 'cases')
APTLY_CONF_TEMPLATE = json.loads(pkgutil.get_data('e2e', 'aptly.conf'))


def idfn(case):
    return case.name

@pytest.mark.parametrize('case', CASES, ids=idfn)
def test_e2e(case, caplog):
    setup_logging()
    caplog.set_level(logging.DEBUG)

    with tempfile.TemporaryDirectory() as root_dir:
        with open(Path(root_dir) / 'aptly.conf', 'w+') as f:
            f.write(json.dumps({**APTLY_CONF_TEMPLATE, 'rootDir': root_dir}))

        context = Context(
            config=f.name,
            formats={
                'snapshot': case.arguments.get('--snapshot-subst', '{name}'),
            },
        )
        formatter = NameFormatter()
        case.expected_output = formatter.format(
            case.expected_output,
            now=context.now,
            random=context.random,
        )

        for step in case.before:
            assert context.execute(step, 0)

        with unittest.mock.patch('allocloud.openapt.Context') as MockContext:
            MockContext.return_value = context

            log_string = io.StringIO()
            handler = create_stream_handler(log_string, logging.INFO, max_level=logging.INFO)

            logger = logging.getLogger()
            logger.addHandler(handler)
            try:
                run(case.schema, limits=case.arguments.get('--limit'))
            finally:
                logger.removeHandler(handler)

            log_contents = log_string.getvalue()
            log_contents = log_contents.replace(f' -config={f.name}', '')
            log_string.close()

            assert case.expected_output == log_contents
