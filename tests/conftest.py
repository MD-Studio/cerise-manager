import docker
import pytest
import random
import time

import cerise_manager.service as cs


@pytest.fixture(scope='session')
def docker_client():
    return docker.from_env()


def clean_up_service(docker_client, srv_name):
    try:
        test_srv = docker_client.containers.get(srv_name)
        test_srv.stop()
        test_srv.remove()
    except docker.errors.NotFound:
        pass


@pytest.fixture(scope='session')
def clean_up(docker_client):
    clean_up_service(docker_client, 'cerise_manager_test_service')
    clean_up_service(docker_client, 'cerise_manager_test_service2')
    clean_up_service(docker_client, 'cerise_manager_test_service3')


@pytest.fixture(scope='session')
def test_image(clean_up):
    """Get a plain cerise image for testing.

    Ignores errors; we may have a local image available already,
    in which case we want to continue, otherwise the other
    tests will fail.
    """
    docker_client = docker.from_env()
    try:
        docker_client.images.pull('mdstudio/cerise:develop')
    except docker.errors.APIError:
        pass
    return 'mdstudio/cerise:develop'


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
