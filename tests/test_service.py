import docker
import json
import os
import pytest
import random
import requests
import sys
import time
from unittest.mock import patch


# clean up any mess left over from previous failed tests
from .clean_up import clean_up
clean_up()

import cerise_manager.service as cs
import cerise_manager.errors as ce
from .clean_up import clean_up_service

from .fixtures import docker_client, test_image


def wait_for_status(container, status):
    while container.status != status:
        time.sleep(0.05)
        container.reload()


@pytest.fixture(scope='session')
def test_port():
    return 29593 + random.randrange(100)


@pytest.fixture(scope='session')
def test_container(request, test_image, test_port, docker_client):
    image = docker_client.images.get(test_image)

    container = docker_client.containers.run(
            image,
            name='cerise_manager_test_service',
            ports={'29593/tcp': ('127.0.0.1', test_port) },
            detach=True)

    wait_for_status(container, 'running')

    yield container

    container.stop()
    container.remove()


@pytest.fixture(scope='session')
def test_service(test_container):
    return cs.get_service('cerise_manager_test_service')


def test_service_exists(test_container):
    exists = cs.service_exists('cerise_manager_test_service')
    assert isinstance(exists, bool)
    assert exists

def test_service_does_not_exist():
    exists = cs.service_exists('does_not_exist')
    assert isinstance(exists, bool)
    assert not exists


def test_get_service(test_container):
    srv = cs.get_service('cerise_manager_test_service')
    assert isinstance(srv, cs.ManagedService)

def test_get_missing_service():
    with pytest.raises(ce.ServiceNotFound):
        cs.get_service('does_not_exist')

def test_service_from_dict(test_container):
    service_dict = {'name': 'cerise_manager_test_service'}
    srv = cs.service_from_dict(service_dict)
    assert isinstance(srv, cs.ManagedService)

def test_missing_service_from_dict():
    with pytest.raises(ce.ServiceNotFound):
        cs.service_from_dict({'name': 'doesnotexist'})

def test_create_service(docker_client):
    srv = cs.create_service('cerise_manager_test_service2',
            'mdstudio/cerise:develop')
    assert isinstance(srv, cs.ManagedService)
    clean_up_service('cerise_manager_test_service2')

def test_create_existing_service(test_container):
    with pytest.raises(ce.ServiceAlreadyExists):
        cs.create_service('cerise_manager_test_service',
                'mdstudio/cerise:develop')

def test_create_service_port_occupied(test_container, test_port):
    with pytest.raises(ce.PortNotAvailable):
        cs.create_service('cerise_manager_test_service2',
                'mdstudio/cerise:develop', test_port)
    clean_up_service('cerise_manager_test_service2')

def test_create_service_auto_port_occupied():
    with patch('cerise_manager.service._RAND_RANGE', 1):
        srv0 = cs.create_service('cerise_manager_test_service2',
                'mdstudio/cerise:develop')
        srv1 = cs.create_service('cerise_manager_test_service3',
                'mdstudio/cerise:develop')
        assert srv0._port != srv1._port
        clean_up_service('cerise_manager_test_service2')
        clean_up_service('cerise_manager_test_service3')

def test_create_two_services_and_destroy(test_container, test_port, docker_client):
    srv = cs.create_service('cerise_manager_test_service2',
            'mdstudio/cerise:develop', test_port+1)
    assert isinstance(srv, cs.ManagedService)
    cs.destroy_service(srv)

    with pytest.raises(docker.errors.NotFound):
        docker_client.containers.get('cerise_manager_test_service2')

def test_create_service_object():
    srv = cs.ManagedService('cerise_manager_test_service', 29593)
    assert srv._name == 'cerise_manager_test_service'
    assert srv._port == 29593

def test_destroy_missing_service():
    srv = cs.ManagedService('non_existing_service', 29593)
    with pytest.raises(ce.ServiceNotFound):
        cs.destroy_service(srv)

def test_require_service(docker_client):
    srv = cs.require_service('cerise_manager_test_service2',
            'mdstudio/cerise:develop')
    assert isinstance(srv, cs.ManagedService)
    clean_up_service('cerise_manager_test_service2')

def test_require_existing_service(docker_client, test_container, test_port):
    srv = cs.require_service('cerise_manager_test_service',
            'mdstudio/cerise:develop')
    assert isinstance(srv, cs.ManagedService)
    assert srv._name == 'cerise_manager_test_service'
    assert srv._port == test_port

def test_require_stopped_service(docker_client, test_container, test_port):
    test_container.stop()
    srv = cs.require_service('cerise_manager_test_service',
            'mdstudio/cerise:develop')
    assert isinstance(srv, cs.ManagedService)
    assert srv._name == 'cerise_manager_test_service'
    assert srv._port == test_port
    assert srv.is_running()

def test_require_server_occupied_port(docker_client, test_container, test_port):
    with pytest.raises(ce.PortNotAvailable):
        srv = cs.require_service('cerise_manager_test_service2',
                'mdstudio/cerise:develop', test_port)

def test_start_running_service(docker_client, test_container, test_service):
    assert test_container.status == 'running'

    test_service.start()

    test_container.reload()
    assert test_container.status == 'running'

def test_start_stopped_service(docker_client, test_container, test_service):
    assert test_container.status == 'running'
    test_container.stop()
    test_container.reload()
    assert test_container.status == 'exited'

    test_service.start()

    test_container.reload()
    assert test_container.status == 'running'

def test_stop_running_service(docker_client, test_container, test_service):
    test_service.stop()

    test_container = docker_client.containers.get('cerise_manager_test_service')
    assert test_container.status == 'exited'
    test_container.start()

def test_stop_stopped_service(docker_client, test_container, test_service):
    test_container.stop()
    test_container.reload()
    assert test_container.status == 'exited'

    test_service.stop()

    test_container.reload()
    assert test_container.status == 'exited'
    test_container.start()
    wait_for_status(test_container, 'running')

def test_service_is_running(docker_client, test_container, test_service):
    assert test_container.status == 'running'
    assert test_service.is_running()

def test_is_not_running(docker_client, test_container, test_service):
    test_container.stop()
    test_container.reload()
    assert test_container.status == 'exited'

    assert not test_service.is_running()
    test_container.start()

def test_service_to_dict(test_service, test_port):
    dict_ = cs.service_to_dict(test_service)
    assert dict_['name'] == 'cerise_manager_test_service'

def test_service_serialisation(test_service, test_port):
    dict_ = cs.service_to_dict(test_service)
    json_dict = json.dumps(dict_)
    dict2 = json.loads(json_dict)
    srv = cs.service_from_dict(dict2)

    assert srv.is_running()
    assert srv._name == 'cerise_manager_test_service'
    assert srv._port == test_port

def test_get_log(test_service):
    # Give it a bit of time to start up, esp. on Travis
    time.sleep(5)
    log = test_service.get_log()
    assert isinstance(log, str) or isinstance(log, unicode)
    assert log != ''
