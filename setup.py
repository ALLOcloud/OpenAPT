#!/usr/bin/python3

import sys

from setuptools import setup, find_namespace_packages

setup(
    name='openapt',
    version='1.0.0',
    description='Specify and automate APT repository management.',
    author='Raphael Medaer',
    author_email='raphael.medaer@allocloud.com',
    classifiers=[
        'Programming Language :: Python :: 3.7',
    ],
    python_requires='>=3.7',
    packages=find_namespace_packages(),
    package_data={
        'allocloud.openapt.specs': [
            '*.json',
        ],
    },
    install_requires=[
        'jsonschema',
        'pyyaml',
    ] if sys.argv[1] != 'test' else [],
    setup_requires=[
        'pytest-runner',
        'pytest-pylint',
    ],
    tests_require=[
        'pytest',
        'pylint',
    ],
    test_suite='tests',
    entry_points={
        'console_scripts': [
            'openapt = allocloud.openapt.__main__:main',
        ]
    },
)
