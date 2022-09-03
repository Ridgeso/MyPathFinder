from setuptools import setup, Extension, find_packages
from Cython.Build import cythonize
import numpy as np


setup(
    packages=find_packages(),
    ext_modules=cythonize([Extension(name="astarc", sources=["astarc.pyx", "tools.c"])]),
    include_dirs=[np.get_include()],
    options={
        "build": {
            "build_lib": "build"
        }
    },
)
