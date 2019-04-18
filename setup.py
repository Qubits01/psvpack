#!/usr/bin/env python3
# pylint: disable=W,C

from setuptools import setup, find_packages
setup(
    name = "psvstore",
    version = "0.190418",
    author = "Qubits",
    author_email = "no@email.com",
    license = "MIT",
    description = "PS Vita pkg fetch tool",
    keywords = "psvita psv vita",
    url = "https://github.com/Qubits01/psvstore",

    packages = find_packages(),
    scripts = [],

    install_requires = ['docutils', 'requests', 'arrow>=0.7.0', 'progressbar2', 'pyyaml'],

    package_data = {
        '': [ '*.md' ],
    },

    entry_points = {
        'console_scripts': [ 'psvstore = psvstore.cli:_main' ],
    }

    # could also include long_description, download_url, classifiers, etc.
)
