OpenAPT
=======

OpenAPT is a description format for APT packages repositories.  
An OpenAPT file allows you to describe the objects and relationships you need to publish and maintain custom repositories through:

* Repositories (a custom set of packages)
* Mirrors
* Snapshots
* Publishings

## Concepts

Currently, most of the concepts used are borrowed to [aptly](https://www.aptly.info/) project nomenclature.  
And under the hood, `openapt` is building all the commands to call `aptly` CLI.

```
user@machine:~$ openapt file.json
```

**TODO**: describe CLI (`--dry-run`, `--debug`, `--snapshot-subst`...)

## File structure

An OpenAPT file is basically a JSON file and looks like the following:

```json
{
  "repositories": {
    "allocloud": {
    }
  },
  "mirrors": {
    "debian_buster": {
      "archive": "http://deb.debian.org/debian",
      "distribution": "buster",
      "filter": "toilet"
    }
  },
  "snapshots": {
    "allocloud": {
      "type": "create",
      "repository": "allocloud"
    },
    "buster": {
      "type": "create",
      "mirror": "debian_buster"
    },
    "openapt": {
      "type": "merge",
      "sources": [
        "allocloud_filtered",
        "buster"
      ]
    },
    "allocloud_filtered": {
      "type": "filter",
      "source": "allocloud",
      "filter": "toilet",
      "withDeps": true
    }
  },
  "publishings": {
    "openapt": {
      "snapshot": "openapt"
    }
  }
}
```

This file is validated against a meta-schema that you can find [here](https://gitlab.eyepea.eu/allocloud/openapt/blob/develop/allocloud/openapt/meta-schema.json).

## Test

To start the test suite, do it using [docker-compose](https://docs.docker.com/compose/):

```bash
user@machine:~$ docker-compose run main python3.7 setup.py test
```
