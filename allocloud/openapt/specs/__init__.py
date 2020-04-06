import json
from pkg_resources import resource_string
from jsonschema import Draft4Validator

from allocloud.openapt.errors import SchemaParseException

SPECS_1_0 = json.loads(resource_string(__name__, 'openapt-specs_1.0.json'))

def validate_schema(schema):
    version = schema.get('openapt')
    if not version:
        raise SchemaParseException([
            {
                'message': 'Could not resolve OpenAPT version',
            }
        ])

    if version == '1.0':
        validator = Draft4Validator(SPECS_1_0)
    else:
        raise SchemaParseException([
            {
                'message': 'Unknown OpenAPT version',
            }
        ])

    errors = list(validator.iter_errors(schema))
    if errors:
        raise SchemaParseException(errors)
