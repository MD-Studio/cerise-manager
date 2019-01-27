import docker
import json
import os
import pytest
import requests
import sys
import time


# clean up any mess left over from previous failed tests
from .clean_up import clean_up
clean_up()

import cerise_manager.service as cs
import cerise_manager.errors as ce
from .clean_up import clean_up_service

from .fixtures import docker_client, test_image, test_service, this_dir
from .fixtures import create_test_job

@pytest.fixture()
def test_container(request, test_image, docker_client):
    try:
        container = docker_client.containers.get('cerise_manager_test_service')
    except docker.errors.NotFound:
        image = docker_client.images.get(test_image)

        container = docker_client.containers.run(
                image,
                name='cerise_manager_test_service',
                ports={'29593/tcp': ('127.0.0.1', 29593) },
                detach=True)

    yield container

    container.stop()
    container.remove()

@pytest.fixture()
def test_service_dict(request):
    return {
            'name': 'cerise_manager_test_service',
            'port': 29593
            }

def test_service_exists(test_container):
    exists = cs.service_exists('cerise_manager_test_service')
    assert isinstance(exists, bool)
    assert exists

def test_service_does_not_exist():
    exists = cs.service_exists('cerise_manager_test_service')
    assert isinstance(exists, bool)
    assert not exists


def test_get_service(test_container):
    srv = cs.get_service('cerise_manager_test_service', 29593)
    assert isinstance(srv, cs.ManagedService)

def test_get_missing_service():
    with pytest.raises(ce.ServiceNotFound):
        cs.get_service('cerise_manager_test_service', 29593)

def test_service_from_dict(test_container, test_service_dict):
    srv = cs.service_from_dict(test_service_dict)
    assert isinstance(srv, cs.ManagedService)

def test_missing_service_from_dict(test_service_dict):
    with pytest.raises(ce.ServiceNotFound):
        cs.service_from_dict(test_service_dict)

def test_create_service(docker_client):
    srv = cs.create_service('cerise_manager_test_service', 29593,
            'mdstudio/cerise:develop')
    assert isinstance(srv, cs.ManagedService)
    clean_up_service('cerise_manager_test_service')

def test_create_existing_service(test_container):
    with pytest.raises(ce.ServiceAlreadyExists):
        cs.create_service('cerise_manager_test_service', 29593,
                'mdstudio/cerise:develop')

def test_create_service_port_occupied(test_container):
    with pytest.raises(ce.PortNotAvailable):
        cs.create_service('cerise_manager_test_service2', 29593,
                'mdstudio/cerise:develop')
    clean_up_service('cerise_manager_test_service2')

def test_create_two_services(test_container):
    srv = cs.create_service('cerise_manager_test_service2', 29594,
            'mdstudio/cerise:develop')
    assert isinstance(srv, cs.ManagedService)
    cs.destroy_service(srv)

def test_create_service_object():
    srv = cs.ManagedService('cerise_manager_test_service', 29593)
    assert srv._name == 'cerise_manager_test_service'
    assert srv._port == 29593

def test_destroy_service(docker_client, test_service):
    container = docker_client.containers.get('cerise_manager_test_service')
    assert container.status == 'running'

    cs.destroy_service(test_service)

    with pytest.raises(docker.errors.NotFound):
        docker_client.containers.get('cerise_manager_test_service')

def test_destroy_missing_service(docker_client):
    srv = cs.ManagedService('non_existing_service', 29593)
    with pytest.raises(ce.ServiceNotFound):
        cs.destroy_service(srv)

def test_require_service(docker_client):
    srv = cs.require_service('cerise_manager_test_service', 29593,
            'mdstudio/cerise:develop')
    assert isinstance(srv, cs.ManagedService)
    clean_up_service('cerise_manager_test_service')

def test_require_existing_service(docker_client, test_service):
    srv = cs.require_service('cerise_manager_test_service', 29593,
            'mdstudio/cerise:develop')
    assert isinstance(srv, cs.ManagedService)
    assert srv._name == 'cerise_manager_test_service'
    assert srv._port == 29593

def test_require_server_occupied_port(docker_client, test_service):
    with pytest.raises(ce.PortNotAvailable):
        srv = cs.require_service('cerise_manager_test_service2', 29593,
                'mdstudio/cerise:develop')

def test_start_running_service(docker_client, test_service):
    container = docker_client.containers.get('cerise_manager_test_service')
    assert container.status == 'running'

    cs.start_service(test_service)

    container.reload()
    assert container.status == 'running'

def test_start_stopped_service(docker_client, test_service):
    container = docker_client.containers.get('cerise_manager_test_service')
    assert container.status == 'running'
    container.stop()
    container.reload()
    assert container.status == 'exited'

    cs.start_service(test_service)

    container.reload()
    assert container.status == 'running'

def test_stop_running_service(docker_client, test_service):
    cs.stop_service(test_service)

    container = docker_client.containers.get('cerise_manager_test_service')
    assert container.status == 'exited'

def test_stop_stopped_service(docker_client, test_service):
    container = docker_client.containers.get('cerise_manager_test_service')
    container.stop()
    container.reload()
    assert container.status == 'exited'

    cs.stop_service(test_service)

    container.reload()
    assert container.status == 'exited'

def test_service_is_running(docker_client, test_service):
    container = docker_client.containers.get('cerise_manager_test_service')
    assert container.status == 'running'
    assert cs.service_is_running(test_service)

def test_is_not_running(docker_client, test_service):
    container = docker_client.containers.get('cerise_manager_test_service')
    container.stop()
    container.reload()
    assert container.status == 'exited'

    assert not cs.service_is_running(test_service)

def test_service_to_dict(test_service):
    dict_ = cs.service_to_dict(test_service)
    assert dict_['name'] == 'cerise_manager_test_service'
    assert dict_['port'] == 29593

def test_service_serialisation(test_service):
    dict_ = cs.service_to_dict(test_service)
    json_dict = json.dumps(dict_)
    dict2 = json.loads(json_dict)
    srv = cs.service_from_dict(dict2)

    assert cs.service_is_running(srv)
    assert srv._name == 'cerise_manager_test_service'
    assert srv._port == 29593

def test_get_log(test_service):
    # Give it a bit of time to start up, esp. on Travis
    time.sleep(5)
    log = test_service.get_log()
    assert isinstance(log, str) or isinstance(log, unicode)
    assert log != ''
