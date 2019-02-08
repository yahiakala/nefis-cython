"""Setup script."""
import os
from setuptools import setup, find_packages


def read(fname):
    """Read readme file."""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="nefiscython",
    version="0.1",
    author="Yahia Kala",
    author_email="noname@noname.com",
    description=("Python wrapper for Nefis Cython library"),
    license="LGPL",
    keywords="NEFIS",
    packages=find_packages(),
    long_description=read('README.md'),
    classifiers=[
        "Natural Language :: English",
        "Programming Language :: Python",
        "License :: Lesser General Public License (LGPL)",
    ],
)
