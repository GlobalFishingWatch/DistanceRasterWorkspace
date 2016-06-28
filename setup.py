#!/usr/bin/env python

from Cython.Build import cythonize
import numpy as np
from setuptools import find_packages
from setuptools import setup
from setuptools.extension import Extension


ext_options = {
    'include_dirs': [np.get_include()]
}

ext_modules = cythonize([
    Extension('distrast._alg', ['distrast/_alg.pyx'], **ext_options)])


setup(
    name='distrast',
    version='0.1',
    description='Distance raster',
    long_description='distance raster',
    ext_modules=ext_modules,
    packages=find_packages(exclude=['test*']))
