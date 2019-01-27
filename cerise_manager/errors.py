class ServiceNotFound(Exception):
    """
    The given service does not exist on this machine. Either it was
    never created, or it was destroyed, or the Docker container running
    it was destroyed by an outside influence.
    """
    pass

class ServiceAlreadyExists(Exception):
    """
    A service with the given name already exists on this machine, so
    another one cannot be created.
    """
    pass

class PortNotAvailable(Exception):
    """
    The requested port is occupied by another service, or by some
    other program that has bound it on localhost. Either stop the
    blocking service or program, or try again with a different
    port number.
    """
    pass

class CommunicationError(Exception):
    """
    There was an error communicating with the service.
    """
    pass
