#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from distutils.core import setup, Command

from innosetup import (__version__, __doc__)


def read_file(name):
    path = os.path.join(os.path.dirname(__file__), name)
    with open(os.path.abspath(path), 'r') as f:
        return f.read()

try:
    readme = read_file('README.rst')
    changes = read_file('CHANGES.rst')
except IOError:
    readme = ""
    changes = ""

project_url = 'https://github.com/Surgo/python-innosetup'

setup(
    name='innosetup',
    version=__version__,
    packages=['innosetup', ],
    author='chrono-meter@gmx.net',
    author_email='chrono-meter@gmx.net',
    url=project_url,
    download_url='%s/zipball/%s' % (project_url, __version__),
    description=__doc__,
    long_description='%s\n\n%s' % (readme, changes),
    keywords=['distutils'],
    install_requires=['pywin32', 'py2exe', ],
    license='PSF',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Environment :: Win32 (MS Windows)',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Python Software Foundation License',
        'Operating System :: Microsoft :: Windows :: Windows NT/2000',
        'Operating System :: Microsoft :: Windows :: Windows XP',
        'Operating System :: Microsoft :: Windows :: Windows 7',
        'Programming Language :: Python :: 2 :: Only',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
