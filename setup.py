#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-

"""Setup file for createm4b"""

from setuptools import setup

setup(name='createm4b',
      version='0.1.0',
      packages=['createm4b'],
      install_requires=['ffmpeg-python'],
      entry_points={
          'console_scripts': [
              'createm4b = createm4b.__main__:main'
          ]
      },
      )
