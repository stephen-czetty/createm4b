#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Setup file for createm4b"""

from setuptools import setup

setup(name='createm4b',
      version='0.1.0',
      packages=['createm4b'],
      install_requires=['eyeD3>=0.8', 'ffmpeg-python'],
      entry_points={
          'console_scripts': [
              'createm4b = createm4b.__main__:main'
          ]
      },
      )
