#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = '0.6.6'


import sys

import distutils.command
from innosetup import (innosetup, DEFAULT_ISS, DEFAULT_CODES)


distutils.command.__all__.append('innosetup')
sys.modules['distutils.command.innosetup'] = sys.modules[__name__]
