import errno
import os
import requests
import tarfile
import tempfile
import time

import docker
import cerise_client.service as ccs

from cerise_manager import errors


# Creating and destroying services

def create_service(srv_name, port, srv_type, user_name=None, password=None):
    """
    Creates a new service for a given user at a given port.

    Args:
        srv_name (str): A unique name for the service. Must be a valid
            Docker container name.
        port (int): A unique port number on which the service will be
            made available. It will listen only on localhost.
        srv_type (str): The type of service to launch. This is the name
            of the Docker image to use.
        user_name (str): The user name to use to connect to the compute
            resource.
        password (str): The password to use to connect to the compute
            resource.

    Returns:
        ManagedService: The created service

    Raises:
        ServiceAlreadyExists: A service with this name already exists.
        PortNotAvailable: The requested port is occupied.
    """
    dc = docker.from_env()

    environment = {}
    environment['CERISE_STORE_LOCATION_CLIENT'] = 'http://localhost:{}/files'.format(port)

    if user_name == '':
        user_name = None

    if user_name is not None:
        environment['CERISE_USERNAME'] = user_name
    if password is not None:
        environment['CERISE_PASSWORD'] = password

    try:
        dc.containers.run(
                srv_type,
                name=srv_name,
                ports={'29593/tcp': ('127.0.0.1', port) },
                environment=environment,
                detach=True)
    except docker.errors.APIError as e:
        # Bit clunky, but it's all Docker gives us...
        if 'address already in use' in e.explanation:
            raise errors.PortNotAvailable(e)
        if 'port is already allocated' in e.explanation:
            raise errors.PortNotAvailable(e)
        if 'Conflict. The container name' in e.explanation:
            raise errors.ServiceAlreadyExists()
        raise

    time.sleep(1)

    return ManagedService(srv_name, port)

def destroy_service(srv):
    """
    Destroys a service.

    This will make the service unavailable, and delete all
    jobs and information about them (including input and output
    data) in this service and on the compute resource, then
    remove the container.

    Args:
        srv (ManagedService): A managed service.

    Raises:
        ServiceNotFound: A service with this name was not found.
    """
    dc = docker.from_env()
    try:
        container = dc.containers.get(srv._name)
        container.stop()
        container.remove()
    except docker.errors.NotFound:
        raise errors.ServiceNotFound()

def service_exists(srv_name):
    """
    Checks whether a managed service with the given name exists.

    Args:
        srv_name (str): Name of the service. Must be a valid Docker
            container name.

    Returns:
        bool: True iff the service exists
    """
    dc = docker.from_env()
    try:
        dc.containers.get(srv_name)
        return True
    except docker.errors.NotFound:
        return False

def get_service(srv_name, port):
    """
    Gets a managed service by name and port.

    Args:
        srv_name (str): Name that the service was created with. Must be
            a valid Docker container name.
        port (int): Port number that the service was created with.

    Returns:
        ManagedService: The service, if it exists.

    Raises:
        ServiceNotFound: The requested service does not exist.
    """
    if not service_exists(srv_name):
        raise errors.ServiceNotFound()
    return ManagedService(srv_name, port)

def require_service(srv_name, port, srv_type, user_name=None, password=None):
    """
    Creates a new service for a given user at a given port, if it does
    not already exist.

    If a service with the given name already exists, it is returned
    instead and no new service is created.

    Args:
        srv_name (str): A unique name for the service. Must be a valid
            Docker container name.
        port (int): A unique port number on which the service will be
            made available. It will listen only on localhost.
        srv_type (str): The type of service to launch. This is the name
            of the Docker image to use.
        user_name (str): The user name to use to connect to the compute
            resource.
        password (str): The password to use to connect to the compute
            resource.

    Returns:
        ManagedService: The created service

    Raises:
        PortNotAvailable: The requested port is occupied.
    """
    try:
        return create_service(srv_name, port, srv_type, user_name, password)
    except errors.ServiceAlreadyExists:
        return get_service(srv_name, port)


# Starting and stopping managed services

def service_is_running(srv):
    """
    Checks whether the managed service is running.

    Returns:
        bool: True iff the service is running.
    """
    dc = docker.from_env()
    container = dc.containers.get(srv._name)
    return container.status == 'running'

def start_service(srv):
    """
    Start a stopped managed service.

    Does nothing if the service is already running.
    """
    dc = docker.from_env()
    container = dc.containers.get(srv._name)
    container.start()
    # Give it some time to start, so subsequent calls work
    time.sleep(1)

def stop_service(srv):
    """
    Stop a running managed service.

    This must be done before shutting down the computer, to ensure
    a clean shutdown. Does nothing if the service is already
    stopped.
    """
    dc = docker.from_env()
    container = dc.containers.get(srv._name)
    container.stop()


# Serialisation of services

def service_to_dict(srv):
    """
    Saves the service to a dictionary.

    The dictionary can later be used to recreate the ManagedService
    object by passing it to service_from_dict(). The exact format of
    the dictionary is not given, but it contains only Python built-in
    types so that it can easily be stored or otherwise serialised.

    Returns:
        dict: A dictionary with information necessary to rebuild
            the ManagedService object.
    """
    return {
            'name': srv._name,
            'port': srv._port
            }

def service_from_dict(srv_dict):
    """
    Gets a service from a dictionary.

    The dictionary must have been created by a call to
    service_to_dict().

    Args:
        srv_dict (dict): A dictionary describing the service.

    Returns:
        ManagedService: The service, if it exists.

    Raises:
        ServiceNotFound: The requested service does not exist.
    """
    return get_service(srv_dict['name'], srv_dict['port'])


class ManagedService(ccs.Service):
    """A managed service in a Docker container.
    """
    def __init__(self, name, port):
        """
        Create a new ManagedService object.

        Note that this does not actually create the Docker container;
        use create_service(), get_service() or service_from_dict() to
        obtain a ManagedService object with an actual corresponding
        service.

        Args:
            name (str): The name for the service (and its corresponding
                Docker container).
            port (int): The port number on which the service runs.
        """
        super().__init__('http://localhost', port)

        self._name = name
        """str: The name of this service, and its Docker container."""
        self._port = port
        """int: The port number this service runs on."""

    def get_log(self):
        """
        Get the internal Cerise log for this service. If things are not
        working as you expect them to (e.g. a job status of
        SystemError), the log may contain useful information on what
        went wrong.

        Returns:
            str: The job log
        """
        dc = docker.from_env()
        container = dc.containers.get(self._name)
        stream, stat = container.get_archive('/var/log/cerise/cerise_backend.log')
        with tempfile.TemporaryFile() as tmp:
            tmp.write(stream.read())
            tmp.seek(0)
            with tarfile.open(fileobj=tmp) as archive:
                # Scope guard does not work in Python 2
                logfile = archive.extractfile('cerise_backend.log')
                service_log = logfile.read().decode('utf-8')
                logfile.close()
        return service_log
