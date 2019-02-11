# -*- coding: utf-8 -*-
"""Documentation about Cerise Manager"""

from .__version__ import __version__

__author__ = "Lourens Veen"
__email__ = 'l.veen@esciencecenter.nl'


from cerise_manager.errors import (
        ServiceNotFound, ServiceAlreadyExists, PortNotAvailable,
        CommunicationError)

from cerise_manager.service import (
        create_service, destroy_service, service_exists, get_service,
        require_service, service_to_dict, service_from_dict, ManagedService)

__all__ = ['ServiceNotFound', 'ServiceAlreadyExists', 'PortNotAvailable',
           'CommunicationError', 'create_service', 'destroy_service',
           'service_exists', 'get_service', 'require_service',
           'service_to_dict', 'service_from_dict', 'ManagedService']
