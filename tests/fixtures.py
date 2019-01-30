import docker
import os
import pytest
import requests
import time

import cerise_manager.service as cs

@pytest.fixture(scope='session')
def docker_client(request):
    return docker.from_env()

@pytest.fixture(scope='session')
def test_image(request):
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
