class OAException(Exception):
    pass

class SchemaParseException(OAException):
    def __init__(self, errors):
        super(SchemaParseException, self).__init__('Invalid schema')
        self.errors = errors

class AptlyException(OAException):
    def __init__(self):
        super(AptlyException, self).__init__('Failed to execute aptly command')

class EntityNotFoundException(OAException):
    def __init__(self):
        super(EntityNotFoundException, self).__init__('Dependency not found')

class CircularDependencyException(OAException):
    def __init__(self):
        super(CircularDependencyException, self).__init__('Circular dependency found')
