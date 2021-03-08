from setuptools import setup, find_packages

from vis5 import __version__


# Don't install requirements if on ReadTheDocs build system.
# Load the PEP508 formatted requirements from the requirements.txt file. Needs
# pip version > 19.0
with open("requirements.txt", "r") as fh:
    requires = fh.readlines()

setup(
    name="vis5",
    version=__version__,
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=requires,
    # metadata for upload to PyPI
    author="Kiyo Masui, J. Richard Shaw",
    author_email="richard@phas.ubc.ca",
    description="vis5 data reader",
    license="MIT",
    url="http://github.com/radiocosmology/vis5",
)
