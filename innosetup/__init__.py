#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""distutils extension module - create an installer by InnoSetup."""

__version__ = '0.6.8'


import sys

import distutils.command
from innosetup import (innosetup, DEFAULT_ISS, DEFAULT_CODES)


distutils.command.__all__.append('innosetup')
sys.modules['distutils.command.innosetup'] = sys.modules[__name__]
