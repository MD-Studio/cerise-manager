.. image:: https://www.travis-ci.org/MD-Studio/cerise-manager.svg?branch=master
    :target: https://www.travis-ci.org/MD-Studio/cerise-manager

##############
Cerise Manager
##############

Cerise Manager is a Python library for managing containerised Cerise instances.
Using Cerise Manager, you can create, destroy, start and stop (specialised)
Cerise instances running on your local machine. Cerise Manager is an extension
of Cerise Client, so you can also submit jobs and manage those on the created
services.

Installation
************

Cerise Manager is on PyPI, so you can just

```
pip install cerise_manager
```

possibly in a virtualenv or Conda environment, if you so desire. Cerise Manager
supports Python 3.4 and up.

Development
***********

To install cerise_manager from GitHub, do:

.. code-block:: console

  git clone https://github.com/MD-Studio/cerise_manager.git
  cd cerise_manager
  pip install .


Run tests (including coverage) with:

.. code-block:: console

  python setup.py test

If you want to contribute to the development of Cerise Manager,
have a look at the `contribution guidelines <CONTRIBUTING.rst>`_.

Documentation
-------------

* Documentation should be put in the ``docs`` folder. The contents have been generated using ``sphinx-quickstart`` (Sphinx version 1.6.5).
* We recommend writing the documentation using Restructured Text (reST) and Google style docstrings.

  - `Restructured Text (reST) and Sphinx CheatSheet <http://openalea.gforge.inria.fr/doc/openalea/doc/_build/html/source/sphinx/rest_syntax.html>`_
  - `Google style docstring examples <http://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html>`_.

* The documentation is set up with the Read the Docs Sphinx Theme.

  - Check out the `configuration options <https://sphinx-rtd-theme.readthedocs.io/en/latest/>`_.

* To generate html documentation run ``python setup.py build_sphinx``

  - This is configured in ``setup.cfg``
  - Alternatively, run ``make html`` in the ``docs`` folder.

Legal
*****

Copyright (c) 2019, Netherlands eScience Center and VU University Amsterdam

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
