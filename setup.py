try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension

from Cython.Build import cythonize

source = ["astarc.pyx"]
ext = [Extension(name="astarc", sources=source)]

setup(ext_modules=cythonize(ext))
