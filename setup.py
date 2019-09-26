#!/usr/bin/python3

from setuptools import setup, find_namespace_packages

setup(
    name='allocloud.openapt',
    version='0.1.0',
    description='Specify and automate APT repository management.',
    author='Raphael Medaer',
    author_email='raphael.medaer@allocloud.com',
    classifiers=[
        'Programming Language :: Python :: 3.7',
    ],
    packages=find_namespace_packages(),
    install_requires=[
    ],
    setup_requires=[
        'pytest-runner',
        'pytest-pylint',
    ],
    tests_require=[
        'pytest',
        'pylint',
    ],
    entry_points={
        'console_scripts': [
            'allocloud.openapt = allocloud.openapt.__main__:main',
        ]
    },
)
