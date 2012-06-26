========
billiard
========

About
-----

`billiard` is a fork of the Python 2.7 `multiprocessing <http://docs.python.org/library/multiprocessing.html>`_
package. The multiprocessing package itself is a renamed and updated version of
R Oudkerk's `pyprocessing <http://pypi.python.org/pypi/processing/>`_ package.
This standalone variant is intended to be compatible with Python 2.4 and 2.5,
and will draw it's fixes/improvements from python-trunk.

- This package would not be possible if not for the contributions of not only
  the current maintainers but all of the contributors to the original pyprocessing
  package listed `here <http://pyprocessing.berlios.de/doc/THANKS.html>`_

- Also it is a fork of the multiprocessin backport package by Christian Heims.

- It includes the no-execv patch contributed by R. Oudkerk.

- And the Pool improvements previously located in `Celery`_.

.. _`Celery`: http://celeryproject.org


Bug reporting
-------------

Please report bugs related to multiprocessing at the
`Python bug tracker <http://bugs.python.org/>`_. Issues related to billiard
should be reported at http://github.com/celery/billiard/issues.
