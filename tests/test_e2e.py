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
from allocloud.openapt.logging import create_stream_handler, setup_logging
from allocloud.openapt import run

AptlyArgument = str
AptlyCommand = List[AptlyArgument]

@dataclass
class Case:
    name: str
    before: List[AptlyCommand]
    schema: str
    arguments: Mapping[str, str]
    expected_output: str

def collect_cases(base_dir):
    cases = []
    for case_dir in os.listdir(base_dir):
        if not os.path.isdir(base_dir / case_dir):
            continue

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

@pytest.mark.parametrize(
    'case',
    collect_cases(Path(__file__).parent / 'e2e' / 'cases'),
    ids=lambda case: case.name
)
def test_e2e(case, caplog):
    setup_logging(debug=True)
    caplog.set_level(logging.DEBUG)

    with tempfile.TemporaryDirectory() as root_dir:
        with open(Path(root_dir) / 'aptly.conf', 'w+') as f:
            f.write(json.dumps({
                **json.loads(pkgutil.get_data('e2e', 'aptly.conf')),
                'rootDir': root_dir
            }))

        context = Context(
            config=f.name,
            update=case.arguments.get('--update', False),
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
