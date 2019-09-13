
class OAException(Exception):
    pass

class EntityNotFoundException(OAException):
    def __init__(self):
        super(EntityNotFound, self).__init__('Dependency not found')

class CircularDependencyException(OAException):
    def __init__(self):
        super(CircularDependencyFound, self).__init__('Circular dependency found')
