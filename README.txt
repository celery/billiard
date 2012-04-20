==================================
python-multiprocessing
==================================

About
-----

`multiprocessing` is a back port of the Python 2.6/3.0 `multiprocessing <http://docs.python.org/library/multiprocessing.html>`_
package. The multiprocessing package itself is a renamed and updated version of 
R Oudkerk's `pyprocessing <http://pypi.python.org/pypi/processing/>`_ package.
This standalone variant is intended to be compatible with Python 2.4 and 2.5, 
and will draw it's fixes/improvements from python-trunk.

This package would not be possible if not for the contributions of not only
the current maintainers but all of the contributors to the original pyprocessing
package listed `here <http://pyprocessing.berlios.de/doc/THANKS.html>`_

The multiprocessing package monkey patches several aspects of the `threading`
module to make it forward compatible with Python 2.6. The patches are 
non-intrusive and don't change existing functions. See `multiprocessing.patch`
for detailed informations.

Please refer to `<http://www.python.org/doc/2.6/library/multiprocessing.html>`_
for more information about the `multiprocessing` package.

Bug reporting
-------------

Please report bugs related to multiprocessing at the `Python bug 
tracker <http://bugs.python.org/>`_. Issues related to the packaging of
multiprocessing should be reported at `<http://code.google.com/p/python-multiprocessing/>`_.

