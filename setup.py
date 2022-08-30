from setuptools import setup, Extension
from Cython.Build import cythonize


setup(
    ext_modules=cythonize([Extension(name="astarc", sources=["astarc.pyx"])]),
    options={
        "build": {
            "build_lib": "build"
        }
    },
)
