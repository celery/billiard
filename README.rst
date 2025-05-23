========
billiard
========

|build-status-lin| |build-status-win| |license| |wheel| |pyversion| |pyimp|

:Version: 4.2.1
:Web: https://billiard.readthedocs.io
:Download: https://pypi.org/project/billiard/
:Source: https://github.com/celery/billiard/
:DeepWiki: |deepwiki|

.. |build-status-lin| image:: https://github.com/celery/billiard/actions/workflows/ci.yaml/badge.svg
    :alt: Build status on Linux
    :target: https://github.com/celery/billiard/actions/workflows/ci.yaml

.. |build-status-win| image:: https://ci.appveyor.com/api/projects/status/github/celery/billiard?png=true&branch=main
    :alt: Build status on Windows
    :target: https://ci.appveyor.com/project/ask/billiard

.. |license| image:: https://img.shields.io/pypi/l/billiard.svg
    :alt: BSD License
    :target: https://opensource.org/licenses/BSD-3-Clause

.. |wheel| image:: https://img.shields.io/pypi/wheel/billiard.svg
    :alt: Billiard can be installed via wheel
    :target: https://pypi.org/project/billiard/

.. |pyversion| image:: https://img.shields.io/pypi/pyversions/billiard.svg
    :alt: Supported Python versions.
    :target: https://pypi.org/project/billiard/

.. |pyimp| image:: https://img.shields.io/pypi/implementation/billiard.svg
    :alt: Support Python implementations.
    :target: https://pypi.org/project/billiard/

.. |deepwiki| image:: https://devin.ai/assets/deepwiki-badge.png
    :alt: Ask http://DeepWiki.com
    :target: https://deepwiki.com/celery/billiard
    :width: 125px

About
-----

``billiard`` is a fork of the Python 2.7 `multiprocessing <https://docs.python.org/library/multiprocessing.html>`_
package. The multiprocessing package itself is a renamed and updated version of
R Oudkerk's `pyprocessing <https://pypi.org/project/processing/>`_ package.
This standalone variant draws its fixes/improvements from python-trunk and provides
additional bug fixes and improvements.

- This package would not be possible if not for the contributions of not only
  the current maintainers but all of the contributors to the original pyprocessing
  package listed `here <http://pyprocessing.berlios.de/doc/THANKS.html>`_.

- Also, it is a fork of the multiprocessing backport package by Christian Heims.

- It includes the no-execv patch contributed by R. Oudkerk.

- And the Pool improvements previously located in `Celery`_.

- Billiard is used in and is a dependency for `Celery`_ and is maintained by the
  Celery team.

.. _`Celery`: http://celeryproject.org

Documentation
-------------

The documentation for ``billiard`` is available on `Read the Docs <https://billiard.readthedocs.io>`_.

Bug reporting
-------------

Please report bugs related to multiprocessing at the
`Python bug tracker <https://bugs.python.org/>`_. Issues related to billiard
should be reported at https://github.com/celery/billiard/issues.

billiard is part of the Tidelift Subscription
---------------------------------------------

The maintainers of ``billiard`` and thousands of other packages are working
with Tidelift to deliver commercial support and maintenance for the open source
dependencies you use to build your applications. Save time, reduce risk, and
improve code health, while paying the maintainers of the exact dependencies you
use. `Learn more`_.

.. _`Learn more`: https://tidelift.com/subscription/pkg/pypi-billiard?utm_source=pypi-billiard&utm_medium=referral&utm_campaign=readme&utm_term=repo
