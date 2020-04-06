OpenAPT
=======

OpenAPT is a description format for APT repositories.
An OpenAPT file allows you to describe the objects and relationships you need to maintain custom APT repositories through:

* (Local) Repositories
* Mirrors
* Snapshots
* Publishings

Most of the concepts and workflows used are borrowed from [aptly entities and transitions](https://www.aptly.info/doc/overview/).

## Specifications

An OpenAPT schema is a structured JSON or YAML file and looks like the following:

```json
{
  "openapt": "1.0",
  "repositories": {
    "mylocalrepo": {
    }
  },
  "mirrors": {
    "debian_buster": {
      "archive": "http://deb.debian.org/debian",
      "distribution": "buster"
    }
  },
  "snapshots": {
    "mylocalrepo": {
      "type": "create",
      "repository": "mylocalrepo"
    },
    "buster": {
      "type": "create",
      "mirror": "debian_buster"
    },
    "mydistro": {
      "type": "merge",
      "sources": [
        "buster_filtered",
        "mylocalrepo"
      ]
    },
    "buster_filtered": {
      "type": "filter",
      "source": "buster",
      "filter": "toilet",
      "withDeps": true
    }
  },
  "publishings": {
    "public": {
      "snapshot": "mydistro",
      "distribution": "buster"
    }
  }
}
```

This file is validated [using a meta-schema](allocloud/openapt/meta-schema.json).

## Implementation

Under the hood, `openapt` is forging `aptly` commands and call its CLI.

Usage:

```
usage: openapt [-h] [--debug] [--config <file>] [--dry-run]
               [--snapshot-subst <template>]
               [--limit <limit-description>]
               <schema>

OpenAPT Aptly implementation.

positional arguments:
  <schema>

optional arguments:
  -h, --help                   show this help message and exit
  --debug
  --config <file>
  --dry-run
  --update                     update package lists from upstream mirrors
  --snapshot-subst <template>  formating string for snapshots (e.g. "{now:date:%Y%d%m_%H%M%S}_{random:.8s}_{name}")
  --limit <limit-description>  limit string (e.g. "publishing:mydistro")
```

Example:

```
openapt --config=aptly.conf --debug myshema.json
```

## Alternatives

  * [pyaptly](https://github.com/adfinis-sygroup/pyaptly)

## Test

To start the test suite, do it using [docker-compose](https://docs.docker.com/compose/):

```bash
user@machine:~$ docker-compose run main python3.7 setup.py test
```
