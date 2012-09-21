import os
import sys
import glob

try:
    from setuptools import setup, Extension, find_packages
except ImportError:
    from distutils.core import setup, Extension, find_packages  # noqa
from distutils.errors import (
    CCompilerError,
    DistutilsExecError,
    DistutilsPlatformError
)
HERE = os.path.dirname(os.path.abspath(__file__))

ext_errors = (CCompilerError, DistutilsExecError, DistutilsPlatformError)
if sys.platform == 'win32' and sys.version_info >= (2, 6):
    # distutils.msvc9compiler can raise IOError if the compiler is missing
    ext_errors += (IOError, )

is_jython = sys.platform.startswith('java')
is_pypy = hasattr(sys, 'pypy_version_info')
is_py3k = sys.version_info[0] == 3

BUILD_WARNING = """

-----------------------------------------------------------------------
WARNING: The C extensions could not be compiled
-----------------------------------------------------------------------

Maybe you do not have a C compiler installed on this system?
The reason was:
%s

This is just a warning as most of the functionality will work even
without the updated C extension.  It will simply fallback to the
built-in _multiprocessing module.  Most notably you will not be able to use
FORCE_EXECV on POSIX systems.  If this is a problem for you then please
install a C compiler or fix the error(s) above.
-----------------------------------------------------------------------

"""

# -*- py3k -*-
extras = {}
if is_py3k:
    extras['use_2to3'] = True

# -*- Distribution Meta -*-

import re
re_meta = re.compile(r'__(\w+?)__\s*=\s*(.*)')
re_vers = re.compile(r'VERSION\s*=\s*\((.*?)\)')
re_doc = re.compile(r'^"""(.+?)"""')
rq = lambda s: s.strip("\"'")


def add_default(m):
    attr_name, attr_value = m.groups()
    return ((attr_name, rq(attr_value)), )


def add_version(m):
    v = list(map(rq, m.groups()[0].split(', ')))
    return (('VERSION', '.'.join(v[0:4]) + ''.join(v[4:])), )


def add_doc(m):
    return (('doc', m.groups()[0]), )

pats = {re_meta: add_default,
        re_vers: add_version,
        re_doc: add_doc}
here = os.path.abspath(os.path.dirname(__file__))
meta_fh = open(os.path.join(here, 'billiard/__init__.py'))
try:
    meta = {}
    for line in meta_fh:
        if line.strip() == '# -eof meta-':
            break
        for pattern, handler in pats.items():
            m = pattern.match(line.strip())
            if m:
                meta.update(handler(m))
finally:
    meta_fh.close()


if sys.version_info < (2, 5):
    raise ValueError('Versions of Python before 2.5 are not supported')

if sys.platform == 'win32':  # Windows
    macros = dict()
    libraries = ['ws2_32']
elif sys.platform.startswith('darwin'):  # Mac OSX
    macros = dict(
        HAVE_SEM_OPEN=1,
        HAVE_SEM_TIMEDWAIT=0,
        HAVE_FD_TRANSFER=1,
        HAVE_BROKEN_SEM_GETVALUE=1
        )
    libraries = []
elif sys.platform.startswith('cygwin'):  # Cygwin
    macros = dict(
        HAVE_SEM_OPEN=1,
        HAVE_SEM_TIMEDWAIT=1,
        HAVE_FD_TRANSFER=0,
        HAVE_BROKEN_SEM_UNLINK=1
        )
    libraries = []
elif sys.platform in ('freebsd4', 'freebsd5', 'freebsd6'):
    # FreeBSD's P1003.1b semaphore support is very experimental
    # and has many known problems. (as of June 2008)
    macros = dict(                  # FreeBSD 4-6
        HAVE_SEM_OPEN=0,
        HAVE_SEM_TIMEDWAIT=0,
        HAVE_FD_TRANSFER=1,
        )
    libraries = []
elif sys.platform in ('freebsd7', 'freebsd8', 'freebsd9', 'freebsd10'):
    macros = dict(                  # FreeBSD 7+
            HAVE_SEM_OPEN=1,
            HAVE_SEM_TIMEDWAIT=1,
            HAVE_FD_TRANSFER=1,
        )
    libraries = []
elif sys.platform.startswith('openbsd'):
    macros = dict(                  # OpenBSD
        HAVE_SEM_OPEN=0,            # Not implemented
        HAVE_SEM_TIMEDWAIT=0,
        HAVE_FD_TRANSFER=1,
        )
    libraries = []
else:                                   # Linux and other unices
    macros = dict(
        HAVE_SEM_OPEN=1,
        HAVE_SEM_TIMEDWAIT=1,
        HAVE_FD_TRANSFER=1
        )
    libraries = ['rt']


if sys.platform == 'win32':
    multiprocessing_srcs = ['Modules/_billiard/multiprocessing.c',
                            'Modules/_billiard/semaphore.c',
                            'Modules/_billiard/pipe_connection.c',
                            'Modules/_billiard/socket_connection.c',
                            'Modules/_billiard/win32_functions.c'
                           ]
else:
    multiprocessing_srcs = ['Modules/_billiard/multiprocessing.c',
                            'Modules/_billiard/socket_connection.c'
                           ]

    if macros.get('HAVE_SEM_OPEN', False):
        multiprocessing_srcs.append('Modules/_billiard/semaphore.c')

long_description = open(os.path.join(HERE, 'README.rst')).read()
long_description += """

===========
Changes
===========

"""
long_description += open(os.path.join(HERE, 'CHANGES.txt')).read()


def run_setup(with_extensions=True):
    extensions = []
    if with_extensions:
        extensions = [
        Extension('_billiard',
                sources=multiprocessing_srcs,
                define_macros=macros.items(),
                libraries=libraries,
                include_dirs=['Modules/_billiard'],
                depends=(glob.glob('Modules/_billiard/*.h') +
                        ['setup.py'])
                ),
        ]
    setup(
        name='billiard',
        version=meta['VERSION'],
        description=meta['doc'],
        long_description=long_description,
        packages=find_packages(exclude=['ez_setup', 'tests', 'tests.*']),
        ext_modules=extensions,
        author=meta['author'],
        author_email=meta['author_email'],
        maintainer=meta['maintainer'],
        maintainer_email=meta['contact'],
        url=meta['homepage'],
        zip_safe=False,
        license='BSD',
        tests_require=['nose', 'nose-cover3'],
        test_suite='nose.collector',
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'Programming Language :: Python',
            'Programming Language :: C',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.5',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.2',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: Implementation :: CPython',
            'Programming Language :: Python :: Implementation :: Jython',
            'Programming Language :: Python :: Implementation :: PyPy',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX',
            'License :: OSI Approved :: BSD License',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Topic :: System :: Distributed Computing',
        ],
        **extras
    )

try:
    run_setup(not (is_jython or is_pypy or is_py3k))
except (Exception, SystemExit):
    import traceback
    sys.stderr.write(BUILD_WARNING % '\n'.join(traceback.format_stack(), ))
    run_setup(False)
