import os
import sys
import glob

try:
    from setuptools import setup, Extension, find_packages
except ImportError:
    from distutils.core import setup, Extension, find_packages

# Python.version.number.internal_revision
VERSION='2.7.3.0'

HERE = os.path.dirname(os.path.abspath(__file__))

# check __version__ in release mode
if len(sys.argv) > 1 and "dist" in sys.argv[1]:
    mp = os.path.join(HERE, "Lib", "billiard", "__init__.py")
    for line in open(mp):
        if line.startswith("__version__"):
            expected = "__version__ = '%s'" % VERSION
            if line.strip() != expected:
                raise ValueError("Version line in %s is wrong: %s\n"
                                 "expected: %s" % 
                                 (mp, line.strip(), expected))
            break


if sys.version_info < (2, 4):
    raise ValueError("Versions of Python before 2.4 are not supported")

if sys.platform == 'win32': # Windows
    macros = dict()
    libraries = ['ws2_32']
elif sys.platform.startswith('darwin'): # Mac OSX
    macros = dict(
        HAVE_SEM_OPEN=1,
        HAVE_SEM_TIMEDWAIT=0,
        HAVE_FD_TRANSFER=1,
        HAVE_BROKEN_SEM_GETVALUE=1
        )
    libraries = []
elif sys.platform.startswith('cygwin'): # Cygwin
    macros = dict(
        HAVE_SEM_OPEN=1,
        HAVE_SEM_TIMEDWAIT=1,
        HAVE_FD_TRANSFER=0,
        HAVE_BROKEN_SEM_UNLINK=1
        )
    libraries = []
elif sys.platform in ('freebsd4', 'freebsd5', 'freebsd6', 'freebsd7', 'freebsd8'):
    # FreeBSD's P1003.1b semaphore support is very experimental
    # and has many known problems. (as of June 2008)
    macros = dict(                  # FreeBSD
        HAVE_SEM_OPEN=0,
        HAVE_SEM_TIMEDWAIT=0,
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


if 0:
    print 'Macros:'
    for name, value in sorted(macros.iteritems()):
        print '\t%s = %r' % (name, value)
    print '\nLibraries:\n\t%r\n' % ', '.join(libraries)
    print '\Sources:\n\t%r\n' % ', '.join(multiprocessing_srcs)


extensions = [
    Extension('_billiard',
              sources=multiprocessing_srcs,
              define_macros=macros.items(),
              libraries=libraries,
              include_dirs=["Modules/_billiard"],
              depends=(glob.glob('Modules/_billiard/*.h') +
                       ['setup.py'])
              ),
    ]

long_description = open(os.path.join(HERE, 'README.txt')).read()
long_description += """
===========
Changes
===========

"""
long_description += open(os.path.join(HERE, 'CHANGES.txt')).read()


setup(
    name='billiard',
    version=VERSION,
    description="Backport of improvements to the multiprocessing package",
    long_description=long_description,
    packages=find_packages(exclude=['ez_setup', 'tests', 'tests.*']),
    ext_modules=extensions,
    author='R Oudkerk / Python Software Foundation',
    author_email='python-dev@python.org',
    maintainer='Ask Solem',
    maintainer_email='ask@celeryproject.org',
    download_url='http://pypi.python.org/pypi/billiard',
    url='http://github.com/ask/billiard',
    license='BSD Licence',
    platforms='Unix and Windows',
    keywords="",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: C',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'License :: OSI Approved :: BSD License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ]
    )

