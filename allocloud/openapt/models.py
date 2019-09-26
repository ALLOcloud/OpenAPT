import errno
import shlex
import select
import logging
import subprocess
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
from allocloud.openapt.errors import EntityNotFoundException, AptlyException

LOGGER = logging.getLogger(__name__)

class Context():
    def __init__(self, binary=None, config=None, dry_run=False):
        self.binary = binary
        self.config = config
        self.dry_run = dry_run

    def command(self, args):
        execute = [(self.binary if self.binary else 'aptly')]

        if self.config:
            execute.append('-config=%s' % shlex.quote(self.config))

        return execute + args

    def execute(self, args, expected_code=0, log_output=True):
        execute = self.command(args)

        LOGGER.info(' '.join(execute))

        if self.dry_run:
            return True

        process = subprocess.Popen(execute, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while process.poll() is None:
            files = [process.stdout, process.stderr]
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

        return process.returncode == expected_code

@dataclass
class Entity(ABC):
    name: str

    @property
    def priority(self):
        return -1

    @abstractmethod
    def run(self, context: Context):
        raise NotImplementedError()

@dataclass
class Repository(Entity):
    comment: Optional[str] = None
    component: Optional[str] = None
    distribution: Optional[str] = None
    architectures: Optional[List[str]] = None

    @property
    def priority(self):
        return 4

    def run(self, context: Context):
        if not context.execute(['repo', 'show', self.name], 1, False):
            return

        extra_args = []
        if self.distribution:
            extra_args.append('-distribution=%s' % shlex.quote(self.distribution))

        if self.architectures:
            extra_args.append('-architectures=%s' % shlex.quote(','.join(self.architectures)))

        if self.component:
            extra_args.append('-component=%s' % shlex.quote(self.component))

        if self.comment:
            extra_args.append('-comment=%s' % shlex.quote(self.comment))

        if not context.execute(extra_args + ['repo', 'create', self.name]):
            raise AptlyException()

@dataclass
class Mirror(Entity):
    archive: str
    distribution: str
    components: Optional[List[str]] = None
    architectures: Optional[List[str]] = None
    filter: Optional[str] = None
    filterWithDeps: bool = False
    withSources: bool = False
    withUdebs: bool = False

    @property
    def priority(self):
        return 3

    def run(self, context: Context):
        if context.execute(['mirror', 'show', self.name], 1, False):
            extra_args = []
            if self.architectures:
                extra_args.append('-architectures=%s' % shlex.quote(','.join(self.architectures)))

            if self.filter:
                extra_args.append('-filter=%s' % shlex.quote(self.filter))

            if self.filterWithDeps:
                extra_args.append('-filter-with-deps')

            if self.withSources:
                extra_args.append('-with-sources')

            if self.withUdebs:
                extra_args.append('-with-udebs')

            if not context.execute(
                    extra_args
                    + ['mirror', 'create', self.name, self.archive, self.distribution]
                    + (self.components if self.components else [])):
                raise AptlyException()

        if not context.execute(['mirror', 'update', self.name]):
            raise AptlyException()

@dataclass
class Snapshot(Entity):

    @property
    def priority(self):
        return 2

    @abstractmethod
    def run(self, context: Context):
        raise NotImplementedError()

@dataclass
class SnapshotRepository(Snapshot):
    repository: str
    architectures: Optional[List[str]] = None

    def run(self, context: Context):
        if not context.execute(['snapshot', 'show', self.name], 1, False):
            return

        extra_args = []
        if self.architectures:
            extra_args.append('-architectures=%s' % shlex.quote(','.join(self.architectures)))

        if not context.execute(extra_args + ['snapshot', 'create', self.name, 'from', 'repo', self.repository]):
            raise AptlyException()

@dataclass
class SnapshotMirror(Snapshot):
    mirror: str
    architectures: Optional[List[str]] = None

    def run(self, context: Context):
        if not context.execute(['snapshot', 'show', self.name], 1, False):
            return

        extra_args = []
        if self.architectures:
            extra_args.append('-architectures=%s' % shlex.quote(','.join(self.architectures)))

        if not context.execute(extra_args + ['snapshot', 'create', self.name, 'from', 'mirror', self.mirror]):
            raise AptlyException()

@dataclass
class SnapshotMerge(Snapshot):
    sources: List[str]
    architectures: Optional[List[str]] = None
    latest: bool = False
    noRemove: bool = False

    def run(self, context: Context):
        if not context.execute(['snapshot', 'show', self.name], 1, False):
            return

        extra_args = []
        if self.architectures:
            extra_args.append('-architectures=%s' % shlex.quote(','.join(self.architectures)))

        if self.latest:
            extra_args.append('-latest')

        if self.noRemove:
            extra_args.append('-no-remove')

        if not context.execute(extra_args + ['snapshot', 'merge', self.name] + self.sources):
            raise AptlyException()

@dataclass
class SnapshotFilter(Snapshot):
    source: str
    filter: str
    architectures: Optional[List[str]] = None
    withDeps: bool = False

    def run(self, context: Context):
        if not context.execute(['snapshot', 'show', self.name], 1, False):
            return

        extra_args = []
        if self.architectures:
            extra_args.append('-architectures=%s' % shlex.quote(','.join(self.architectures)))

        if self.withDeps:
            extra_args.append('-with-deps')

        if not context.execute(extra_args + ['snapshot', 'filter', self.source, self.name, self.filter]):
            raise AptlyException()

class EntityCollection(list):
    def search(self, name, classinfo):
        try:
            return next(entity for entity in self if isinstance(entity, classinfo) and entity.name == name)
        except StopIteration:
            raise EntityNotFoundException()

    def load(self, schema):
        for name, params in schema.get('repositories').items():
            self.append(Repository(name=name, **params))

        for name, params in schema.get('mirrors').items():
            self.append(Mirror(name=name, **params))

        for name, params in schema.get('snapshots').items():
            action = params.pop('type')
            if action == 'create' and params.get('repository') is not None:
                self.append(SnapshotRepository(name=name, **params))
            elif action == 'create' and params.get('mirror') is not None:
                self.append(SnapshotMirror(name=name, **params))
            elif action == 'filter':
                self.append(SnapshotFilter(name=name, **params))
            elif action == 'merge':
                self.append(SnapshotMerge(name=name, **params))
